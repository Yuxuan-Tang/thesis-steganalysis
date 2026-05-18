#!/usr/bin/env python
"""Create additional synthetic LSB cover/secret pairs for thesis analysis."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(r"D:\thesis")
OUT = ROOT / "experiments" / "inputs" / "lsb_extra"
SIZE = 512


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path)
    return path


def gradient_cover() -> Image.Image:
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    y = np.linspace(0, 1, SIZE)[:, None]
    x = np.linspace(0, 1, SIZE)[None, :]
    arr[..., 0] = (80 + 120 * x).astype(np.uint8)
    arr[..., 1] = (120 + 90 * y).astype(np.uint8)
    arr[..., 2] = (180 + 50 * (1 - x * y)).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    draw = ImageDraw.Draw(img)
    for i in range(0, SIZE, 38):
        draw.arc((i - 120, 210, i + 120, 430), 200, 340, fill=(235, 245, 255), width=2)
    return img


def texture_cover() -> Image.Image:
    rng = np.random.default_rng(20260503)
    base = rng.normal(128, 34, (SIZE, SIZE, 3)).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(base, "RGB").filter(ImageFilter.GaussianBlur(radius=0.6))
    draw = ImageDraw.Draw(img)
    for x in range(-SIZE, SIZE, 28):
        draw.line((x, 0, x + SIZE, SIZE), fill=(165, 145, 112), width=2)
    return img


def city_cover() -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE), "#b9d7ef")
    draw = ImageDraw.Draw(img)
    for y in range(SIZE):
        t = y / SIZE
        draw.line((0, y, SIZE, y), fill=(int(185 - 60 * t), int(215 - 70 * t), int(239 - 75 * t)))
    rng = np.random.default_rng(31415)
    x = 0
    while x < SIZE:
        w = int(rng.integers(34, 72))
        h = int(rng.integers(120, 340))
        color = tuple(int(v) for v in rng.integers(65, 130, 3))
        draw.rectangle((x, SIZE - h, x + w, SIZE), fill=color)
        for wx in range(x + 8, x + w - 8, 14):
            for wy in range(SIZE - h + 12, SIZE - 18, 24):
                draw.rectangle((wx, wy, wx + 6, wy + 10), fill=(230, 224, 154))
        x += w + int(rng.integers(4, 12))
    return img


def wave_cover() -> Image.Image:
    arr = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    waves = 0.5 + 0.5 * np.sin(xx / 23.0 + yy / 37.0)
    arr[..., 0] = (35 + 40 * waves).astype(np.uint8)
    arr[..., 1] = (110 + 80 * waves).astype(np.uint8)
    arr[..., 2] = (165 + 70 * waves).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    draw = ImageDraw.Draw(img)
    for y in range(80, SIZE, 55):
        draw.arc((-40, y, SIZE + 40, y + 90), 8, 172, fill=(218, 246, 255), width=3)
    return img


def secret_card(label: str, shape: str) -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE), "white")
    draw = ImageDraw.Draw(img)
    title = font(58, bold=True)
    small = font(30, bold=True)
    draw.rectangle((46, 46, 466, 466), outline="black", width=8)
    draw.text((82, 72), "LSB PAYLOAD", fill="black", font=small)
    if shape == "circle":
        draw.ellipse((150, 155, 362, 367), outline="black", width=16)
        draw.line((256, 155, 256, 367), fill="black", width=10)
    elif shape == "grid":
        for x in range(142, 371, 57):
            draw.line((x, 150, x, 378), fill="black", width=10)
        for y in range(150, 379, 57):
            draw.line((142, y, 370, y), fill="black", width=10)
    elif shape == "triangle":
        draw.polygon([(256, 138), (382, 368), (130, 368)], outline="black")
        draw.line((256, 138, 382, 368), fill="black", width=16)
        draw.line((382, 368, 130, 368), fill="black", width=16)
        draw.line((130, 368, 256, 138), fill="black", width=16)
    else:
        for r in range(35, 155, 24):
            box = (256 - r, 260 - r, 256 + r, 260 + r)
            draw.arc(box, 0, 300, fill="black", width=10)
    bbox = draw.textbbox((0, 0), label, font=title)
    draw.text(((SIZE - bbox[2] + bbox[0]) / 2, 390), label, fill="black", font=title)
    return img


def main() -> None:
    cases = [
        ("lsb_extra_gradient_badge", gradient_cover(), secret_card("BADGE", "circle")),
        ("lsb_extra_texture_grid", texture_cover(), secret_card("GRID", "grid")),
        ("lsb_extra_city_triangle", city_cover(), secret_card("ALERT", "triangle")),
        ("lsb_extra_wave_spiral", wave_cover(), secret_card("CODE", "spiral")),
    ]
    for name, cover, secret in cases:
        cover_path = save(cover, f"{name}_cover_input.png")
        secret_path = save(secret, f"{name}_secret_input.png")
        print(f"{name}\t{cover_path}\t{secret_path}")


if __name__ == "__main__":
    main()
