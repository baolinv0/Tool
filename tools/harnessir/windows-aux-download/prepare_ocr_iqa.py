"""Prepare PaddleOCR / PyIQA model caches on Windows. Does NOT run restoration benchmarks."""
import argparse
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['ocr', 'iqa', 'report'], required=True)
parser.add_argument('--root', required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
ckpt = root / 'checkpoints'
ckpt.mkdir(parents=True, exist_ok=True)
os.environ['PADDLE_PDX_CACHE_HOME'] = str(ckpt / 'paddleocr')
os.environ['TORCH_HOME'] = str(ckpt / 'torch')
(ckpt / 'paddleocr').mkdir(parents=True, exist_ok=True)
(ckpt / 'torch').mkdir(parents=True, exist_ok=True)
logfile = root / 'pretest_download_status.json'
try:
    status = json.loads(logfile.read_text(encoding='utf-8'))
except (FileNotFoundError, json.JSONDecodeError):
    status = {}

if args.mode == 'ocr':
    try:
        from paddleocr import PaddleOCR
        _ = PaddleOCR(
            text_detection_model_name='PP-OCRv6_medium_det',
            text_recognition_model_name='PP-OCRv6_medium_rec',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        status['ocr'] = {'ok': True, 'note': 'PaddleOCR initialized; cached artifacts in PADDLE_PDX_CACHE_HOME (exact layout may vary by version).'}
        print('OCR initialized and model weights resolved.')
    except Exception as exc:
        status['ocr'] = {'ok': False, 'error': repr(exc)}
        print(f'OCR setup failed: {exc!r}')
        logfile.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        raise
elif args.mode == 'iqa':
    import torch
    import pyiqa
    # Metric IDs are from PyIQA; check installed version for availability.
    requested = ['maniqa', 'clipiqa', 'musiq', 'topiq_nr', 'afine', 'lpips', 'dists']
    available = set(pyiqa.list_models())
    results = {}
    for metric in requested:
        if metric not in available:
            results[metric] = {'ok': False, 'reason': 'not available in installed pyiqa; inspect pyiqa.list_models()'}
            print(f'SKIP {metric}: unavailable')
            continue
        try:
            _ = pyiqa.create_metric(metric, device='cpu')
            results[metric] = {'ok': True}
            print(f'OK {metric}')
        except Exception as exc:
            results[metric] = {'ok': False, 'error': repr(exc)}
            print(f'FAILED {metric}: {exc!r}')
    status['iqa'] = results
    if not all(v['ok'] for v in results.values()):
        print('WARNING: not all requested metrics are ready.')
else:
    expected = {
        'depth_anything_v2_base': ckpt / 'depth_anything_v2_base' / 'model.safetensors',
        'scrfd_det_10g': ckpt / 'insightface' / 'models' / 'buffalo_l' / 'det_10g.onnx',
        'sam3_official_snapshot': ckpt / 'sam3_official',
        'sam3_harness_compatible': ckpt / 'sam3_semantic.pt',
        'paddleocr_cache': ckpt / 'paddleocr',
        'pyiqa_cache': ckpt / 'torch',
    }
    status['files'] = {name: {'exists': path.exists(), 'path': str(path)} for name, path in expected.items()}
    # Directory presence does NOT mean downloaded weights exist.
    status['note'] = 'File existence is only a precheck; model load and run-time compatibility remain unverified.'
    print(json.dumps(status, ensure_ascii=False, indent=2))
logfile.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
if args.mode == 'report':
    (root / 'pretest_assets_report.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
