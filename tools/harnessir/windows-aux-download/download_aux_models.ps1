param(
    [string]$Root = 'D:\HarnessIR',
    [switch]$SkipSam3,
    [switch]$SkipIqa,
    [switch]$SkipOcr,
    [switch]$SkipFace,
    [switch]$SkipDepth
)
$ErrorActionPreference = 'Stop'
$Root = [System.IO.Path]::GetFullPath($Root)
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$checkpoint = Join-Path $Root 'checkpoints'
New-Item -ItemType Directory -Force -Path $checkpoint | Out-Null
$env:HARNESS_CKPT_DIR = $checkpoint
$env:PADDLE_PDX_CACHE_HOME = (Join-Path $checkpoint 'paddleocr')
$env:TORCH_HOME = (Join-Path $checkpoint 'torch')
$env:HF_HOME = (Join-Path $Root 'hf_cache')
foreach ($p in @($env:PADDLE_PDX_CACHE_HOME, $env:TORCH_HOME, $env:HF_HOME)) {
    New-Item -ItemType Directory -Force -Path $p | Out-Null
}
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw 'Python not found on PATH. Activate your Python/Conda environment.' }
& python -c "import huggingface_hub; print('huggingface_hub ready')"
if ($LASTEXITCODE -ne 0) { throw 'Run: python -m pip install -U huggingface_hub' }

function Get-HFSnapshot([string]$Repo, [string]$Target) {
    Write-Host "Downloading $Repo -> $Target"
    $env:_MODEL_REPO = $Repo
    $env:_MODEL_TARGET = $Target
    & python -c "import os; from huggingface_hub import snapshot_download; print(snapshot_download(repo_id=os.environ['_MODEL_REPO'],local_dir=os.environ['_MODEL_TARGET']))"
    if ($LASTEXITCODE -ne 0) { throw "Failed to download $Repo. If gated, obtain access and run: hf auth login" }
}
if (-not $SkipDepth) {
    Get-HFSnapshot 'depth-anything/Depth-Anything-V2-Base-hf' (Join-Path $checkpoint 'depth_anything_v2_base')
}
if (-not $SkipSam3) {
    # SAM3 author code may expect a particular .pt format. Keep the official repo snapshot intact.
    Get-HFSnapshot 'facebook/sam3' (Join-Path $checkpoint 'sam3_official')
    Write-Warning 'SAM3 downloaded, but HarnessIR expects sam3_semantic.pt. Verify checkpoint format/compatibility; do not rename blindly.'
}
if (-not $SkipFace) {
    $faceDir = Join-Path $checkpoint 'insightface\models\buffalo_l'
    New-Item -ItemType Directory -Force -Path $faceDir | Out-Null
    $zip = Join-Path $Root 'buffalo_l.zip'
    Invoke-WebRequest -Uri 'https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip' -OutFile $zip
    $tmp = Join-Path $Root '_buffalo_extract'
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $det = Get-ChildItem -Path $tmp -Recurse -Filter 'det_10g.onnx' | Select-Object -First 1
    if (-not $det) { throw 'buffalo_l.zip did not contain det_10g.onnx' }
    Copy-Item $det.FullName (Join-Path $faceDir 'det_10g.onnx') -Force
    Remove-Item $tmp -Force -Recurse
    Write-Host "Face detector downloaded: $faceDir"
}
$helper = Join-Path $PSScriptRoot 'prepare_ocr_iqa.py'
if (-not (Test-Path $helper)) { throw "Missing $helper. Put both scripts in same folder." }
if (-not $SkipOcr) {
    & python $helper --mode ocr --root $Root
    if ($LASTEXITCODE -ne 0) { Write-Warning 'OCR setup failed. See Python dependency or PaddlePaddle compatibility errors above.' }
}
if (-not $SkipIqa) {
    & python $helper --mode iqa --root $Root
    if ($LASTEXITCODE -ne 0) { Write-Warning 'Some IQA weights failed; inspect pretest_assets_report.json.' }
}
& python $helper --mode report --root $Root
Write-Host "Done. Check $Root\pretest_assets_report.json"
