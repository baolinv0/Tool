# Windows PowerShell 5.1 / PowerShell 7+
# Downloads PaddleOCR PP-OCRv6 medium detector + recognizer (six inference files).
param(
    [string]$Root = "$PWD\checkpoints\paddleocr\official_models"
)

$ErrorActionPreference = 'Stop'
$files = @('inference.pdiparams', 'inference.json', 'inference.yml')
$models = @('PP-OCRv6_medium_det', 'PP-OCRv6_medium_rec')
$rootPath = [System.IO.Path]::GetFullPath($Root)

if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
    throw 'curl.exe not found. Install curl or use Windows 10/11 built-in curl.exe.'
}

foreach ($model in $models) {
    $modelDir = Join-Path $rootPath $model
    New-Item -ItemType Directory -Force -Path $modelDir | Out-Null
    foreach ($file in $files) {
        $target = Join-Path $modelDir $file
        $url = "https://huggingface.co/PaddlePaddle/$model/resolve/main/$file?download=true"
        if ((Test-Path $target) -and (Get-Item $target).Length -gt 0) {
            Write-Host "[SKIP] $model/$file (already exists)"
            continue
        }
        $temp = "$target.part"
        Write-Host "[GET] $model/$file"
        & curl.exe --fail --location --retry 5 --retry-delay 3 --connect-timeout 30 --output $temp $url
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $temp) -or (Get-Item $temp).Length -eq 0) {
            Remove-Item $temp -ErrorAction SilentlyContinue
            throw "Download failed: $url"
        }
        Move-Item -Force $temp $target
        Write-Host "[OK] $target"
    }
}

Write-Host "`nFinished. Files saved to: $rootPath"
Get-ChildItem -Path $rootPath -Recurse -File | Select-Object FullName,Length
