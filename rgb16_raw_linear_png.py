#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RGB16 RAW / linear PNG conversion utility.

Data convention:
- Shape: H x W x 3
- Channel order in memory: RGB
- Scalar type: unsigned 16-bit integer
- Default RAW layout: interleaved RGBRGBRGB...
- Default RAW byte order: little-endian
- PNG values are written without gamma/tone-mapping conversion.

Dependency:
    pip install numpy opencv-python
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

import cv2
import numpy as np


Endian = Literal["little", "big"]
Layout = Literal["interleaved", "planar"]


def _validate_rgb16(rgb: np.ndarray) -> None:
    """Validate an HxWx3 uint16 RGB image."""
    if not isinstance(rgb, np.ndarray):
        raise TypeError(f"rgb must be numpy.ndarray, got {type(rgb)!r}")
    if rgb.dtype != np.uint16:
        raise TypeError(f"rgb dtype must be np.uint16, got {rgb.dtype}")
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"rgb shape must be HxWx3, got {rgb.shape}")


def _dtype_from_endian(endian: Endian) -> np.dtype:
    if endian == "little":
        return np.dtype("<u2")
    if endian == "big":
        return np.dtype(">u2")
    raise ValueError(f"Unsupported endian: {endian}")


def save_rgb16_raw(
    rgb: np.ndarray,
    raw_path: str | Path,
    *,
    endian: Endian = "little",
    layout: Layout = "interleaved",
) -> None:
    """
    Save an HxWx3 uint16 RGB image as a headerless RAW file.

    interleaved:
        R0 G0 B0 R1 G1 B1 ...

    planar:
        all R samples, then all G samples, then all B samples
    """
    _validate_rgb16(rgb)

    raw_path = Path(raw_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    file_dtype = _dtype_from_endian(endian)

    if layout == "interleaved":
        output = np.ascontiguousarray(rgb).astype(file_dtype, copy=False)
    elif layout == "planar":
        output = np.ascontiguousarray(rgb.transpose(2, 0, 1)).astype(
            file_dtype, copy=False
        )
    else:
        raise ValueError(f"Unsupported layout: {layout}")

    output.tofile(raw_path)


def load_rgb16_raw(
    raw_path: str | Path,
    *,
    width: int,
    height: int,
    endian: Endian = "little",
    layout: Layout = "interleaved",
) -> np.ndarray:
    """
    Load a headerless RGB16 RAW file and return an HxWx3 np.uint16 RGB image.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be positive, got {width}x{height}")

    raw_path = Path(raw_path)
    if not raw_path.is_file():
        raise FileNotFoundError(raw_path)

    expected_values = width * height * 3
    expected_bytes = expected_values * 2
    actual_bytes = raw_path.stat().st_size

    if actual_bytes != expected_bytes:
        raise ValueError(
            "RAW file size mismatch: "
            f"expected {expected_bytes} bytes for {width}x{height} RGB16, "
            f"got {actual_bytes} bytes"
        )

    file_dtype = _dtype_from_endian(endian)
    data = np.fromfile(raw_path, dtype=file_dtype, count=expected_values)

    # Convert to native-endian uint16 for subsequent processing.
    data = data.astype(np.uint16, copy=False)

    if layout == "interleaved":
        rgb = data.reshape(height, width, 3)
    elif layout == "planar":
        rgb = data.reshape(3, height, width).transpose(1, 2, 0)
    else:
        raise ValueError(f"Unsupported layout: {layout}")

    return np.ascontiguousarray(rgb)


def save_rgb16_linear_png(
    rgb: np.ndarray,
    png_path: str | Path,
    *,
    compression: int = 3,
) -> None:
    """
    Save RGB uint16 data as a 16-bit three-channel PNG.

    No gamma encoding, tone mapping, normalization, clipping, or bit shifting
    is applied. OpenCV expects BGR channel order, so RGB is converted to BGR
    only for file encoding.
    """
    _validate_rgb16(rgb)

    if not 0 <= compression <= 9:
        raise ValueError("PNG compression must be in [0, 9]")

    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ok = cv2.imwrite(
        str(png_path),
        bgr,
        [cv2.IMWRITE_PNG_COMPRESSION, compression],
    )
    if not ok:
        raise IOError(f"Failed to write PNG: {png_path}")


def load_rgb16_png(png_path: str | Path) -> np.ndarray:
    """Read a 16-bit RGB PNG without reducing it to 8-bit."""
    png_path = Path(png_path)
    bgr = cv2.imread(str(png_path), cv2.IMREAD_UNCHANGED)

    if bgr is None:
        raise IOError(f"Failed to read PNG: {png_path}")
    if bgr.dtype != np.uint16:
        raise TypeError(f"PNG is not uint16, got {bgr.dtype}")
    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError(f"PNG is not a three-channel image, got {bgr.shape}")

    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def raw_to_raw_and_png(
    input_raw: str | Path,
    output_raw: str | Path,
    output_png: str | Path,
    *,
    width: int,
    height: int,
    endian: Endian = "little",
    layout: Layout = "interleaved",
    verify: bool = True,
) -> np.ndarray:
    """
    Read RGB16 RAW, re-save it as RAW, and save the same numerical data as
    a 16-bit linear PNG.
    """
    rgb = load_rgb16_raw(
        input_raw,
        width=width,
        height=height,
        endian=endian,
        layout=layout,
    )

    save_rgb16_raw(rgb, output_raw, endian=endian, layout=layout)
    save_rgb16_linear_png(rgb, output_png)

    if verify:
        reloaded_raw = load_rgb16_raw(
            output_raw,
            width=width,
            height=height,
            endian=endian,
            layout=layout,
        )
        reloaded_png = load_rgb16_png(output_png)

        if not np.array_equal(rgb, reloaded_raw):
            raise RuntimeError("RAW round-trip verification failed")
        if not np.array_equal(rgb, reloaded_png):
            max_error = int(
                np.max(
                    np.abs(rgb.astype(np.int32) - reloaded_png.astype(np.int32))
                )
            )
            raise RuntimeError(
                f"PNG round-trip verification failed; max error = {max_error}"
            )

    return rgb


def array_to_raw_then_reload_and_export(
    rgb16: np.ndarray,
    first_raw: str | Path,
    second_raw: str | Path,
    output_png: str | Path,
    *,
    endian: Endian = "little",
    layout: Layout = "interleaved",
) -> np.ndarray:
    """
    Complete requested flow:

        uint16 RGB array
        -> save *.raw
        -> read *.raw
        -> re-save *.raw
        -> save 16-bit linear *.png
    """
    _validate_rgb16(rgb16)
    height, width, _ = rgb16.shape

    save_rgb16_raw(rgb16, first_raw, endian=endian, layout=layout)

    return raw_to_raw_and_png(
        first_raw,
        second_raw,
        output_png,
        width=width,
        height=height,
        endian=endian,
        layout=layout,
        verify=True,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read RGB16 RAW, re-save RAW, and export a 16-bit linear PNG."
    )
    parser.add_argument("input_raw", type=Path)
    parser.add_argument("output_raw", type=Path)
    parser.add_argument("output_png", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument(
        "--endian",
        choices=("little", "big"),
        default="little",
    )
    parser.add_argument(
        "--layout",
        choices=("interleaved", "planar"),
        default="interleaved",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip exact RAW/PNG round-trip verification.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    rgb = raw_to_raw_and_png(
        args.input_raw,
        args.output_raw,
        args.output_png,
        width=args.width,
        height=args.height,
        endian=args.endian,
        layout=args.layout,
        verify=not args.no_verify,
    )

    print(
        f"Done: shape={rgb.shape}, dtype={rgb.dtype}, "
        f"range=[{int(rgb.min())}, {int(rgb.max())}]"
    )
    print(f"RAW: {args.output_raw}")
    print(f"PNG: {args.output_png}")


if __name__ == "__main__":
    main()
