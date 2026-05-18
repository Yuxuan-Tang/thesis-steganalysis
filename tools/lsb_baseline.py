#!/usr/bin/env python
"""Create a simple LSB steganography baseline for thesis comparison.

This script is intentionally lightweight: it embeds a resized secret image into
the least significant bit of a cover image and writes visual artifacts that make
pixel-level modification traces easy to discuss in the thesis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw


def load_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if size is not None:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return image


def make_histogram(image: Image.Image, out_path: Path, title: str) -> None:
    gray = image.convert("L")
    hist = gray.histogram()
    width, height = 512, 280
    margin = 32
    chart = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(chart)
    max_count = max(hist) or 1

    draw.text((margin, 8), title, fill=(20, 20, 20))
    x0, y0 = margin, height - margin
    x1, y1 = width - margin, 36
    draw.line((x0, y0, x1, y0), fill=(0, 0, 0))
    draw.line((x0, y0, x0, y1), fill=(0, 0, 0))

    for i, count in enumerate(hist):
        x = x0 + int(i * (x1 - x0) / 255)
        bar_h = int(count / max_count * (y0 - y1))
        draw.line((x, y0, x, y0 - bar_h), fill=(54, 92, 150))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    chart.save(out_path)


def amplify_difference(a: Image.Image, b: Image.Image, factor: int = 32) -> Image.Image:
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    arr = np.asarray(diff, dtype=np.uint16) * factor
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def embed_secret_lsb(cover: Image.Image, secret: Image.Image) -> Image.Image:
    cover_arr = np.asarray(cover, dtype=np.uint8).copy()
    secret_arr = np.asarray(secret.convert("L"), dtype=np.uint8)
    secret_bits = (secret_arr > 127).astype(np.uint8)

    # Put one bit of the binarized secret into the red-channel LSB.
    cover_arr[:, :, 0] = (cover_arr[:, :, 0] & 0xFE) | secret_bits
    return Image.fromarray(cover_arr, "RGB")


def recover_secret_lsb(stego: Image.Image) -> Image.Image:
    arr = np.asarray(stego.convert("RGB"), dtype=np.uint8)
    secret = (arr[:, :, 0] & 1) * 255
    return Image.fromarray(secret.astype(np.uint8), "L")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--secret", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("experiments/lsb_outputs"), type=Path)
    parser.add_argument("--name", default="lsb_case")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cover = load_rgb(args.cover)
    secret = load_rgb(args.secret, cover.size)
    stego = embed_secret_lsb(cover, secret)
    recovered = recover_secret_lsb(stego)
    residual = amplify_difference(cover, stego)

    cover.save(out_dir / f"{args.name}_cover.png")
    secret.save(out_dir / f"{args.name}_secret_resized.png")
    stego.save(out_dir / f"{args.name}_lsb_stego.png")
    recovered.save(out_dir / f"{args.name}_lsb_recovered.png")
    residual.save(out_dir / f"{args.name}_lsb_residual_x32.png")
    make_histogram(cover, out_dir / f"{args.name}_cover_hist.png", "Cover grayscale histogram")
    make_histogram(stego, out_dir / f"{args.name}_lsb_stego_hist.png", "LSB stego grayscale histogram")

    print(f"Wrote LSB baseline artifacts to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
