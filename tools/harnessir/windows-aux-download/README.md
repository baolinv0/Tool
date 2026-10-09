# HarnessIR Windows auxiliary model downloader

Downloads/prepares auxiliary checkpoints for [PolyU-VCLab/HarnessIR](https://github.com/PolyU-VCLab/HarnessIR) on Windows. **Does not download the main VLM or image editing executors. Does not run restoration tests.**

## Contents
- `download_aux_models.ps1`: downloads Depth Anything V2 Base, gated SAM 3 snapshot, SCRFD buffalo_l; invokes Python helper.
- `prepare_ocr_iqa.py`: initializes PP-OCRv6 medium detector/recognizer and PyIQA metrics, writes pretest status JSON.

## Usage (PowerShell)
Use Python 3.11 in an isolated environment and install dependencies appropriate to Windows and your CPU/GPU:
```powershell
conda create -n harness-download python=3.11 -y
conda activate harness-download
python -m pip install -U huggingface_hub paddleocr paddlepaddle torch torchvision pyiqa
hf auth login  # required for gated SAM 3, after obtaining approval
Set-ExecutionPolicy -Scope Process Bypass
.\download_aux_models.ps1 -Root "D:\HarnessIR"
```

If SAM 3 access is not approved:
```powershell
.\download_aux_models.ps1 -Root "D:\HarnessIR" -SkipSam3
```

Other switches: `-SkipIqa`, `-SkipOcr`, `-SkipFace`, `-SkipDepth`.

Outputs under `D:\HarnessIR\checkpoints` and status JSON at `D:\HarnessIR\pretest_assets_report.json`.

## Important limitations
1. The official `facebook/sam3` snapshot is **not automatically equivalent** to the `sam3_semantic.pt` expected by HarnessIR. Adapt/verify the loader first; do not rename weights blindly.
2. OCR / PyIQA downloads are triggered by model initialization; the real cache layout depends on installed versions. The report checks paths, **not model inference**.
3. PyIQA model identifiers can change between releases. Unavailable IDs are marked SKIP and are not silently substituted.
4. Check the InsightFace model weight license before commercial use.
5. Scripts have not been run end-to-end on a Windows machine; run in a clean environment and review the status report.
6. Preserve the upstream scripts under this folder; no model weights or download archives are committed to Git.

Source package: `harnessir_windows_aux_download.zip` produced 2026-10-09.
