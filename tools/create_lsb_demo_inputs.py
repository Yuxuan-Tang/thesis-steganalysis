#!/usr/bin/env python
"""Create clear demo inputs for the LSB baseline.

The cover is a simple synthetic landscape and the secret is a high-contrast
binary "SECRET" card. This makes the LSB comparison figure easier to explain:
cover and stego should look almost identical, while the recovered image is the
hidden secret extracted from the least significant bits.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def create_landscape(path: Path, size: int = 512) -> None:
    img = Image.new("RGB", (size, size), "#9fd3ff")
    draw = ImageDraw.Draw(img)

    for y in range(size):
        t = y / size
        r = int(150 * (1 - t) + 238 * t)
        g = int(207 * (1 - t) + 244 * t)
        b = int(255 * (1 - t) + 255 * t)
        draw.line((0, y, size, y), fill=(r, g, b))

    draw.ellipse((360, 50, 455, 145), fill="#ffd36a")
    draw.polygon([(0, 292), (128, 128), (260, 292)], fill="#6f8f9a")
    draw.polygon([(80, 292), (260, 92), (444, 292)], fill="#557282")
    draw.polygon([(220, 292), (395, 145), (512, 292)], fill="#76939c")
    draw.polygon([(128, 128), (93, 174), (158, 174)], fill="#f7fbff")
    draw.polygon([(260, 92), (213, 158), (304, 158)], fill="#f7fbff")
    draw.polygon([(395, 145), (358, 190), (432, 190)], fill="#f7fbff")
    draw.rectangle((0, 292, size, 350), fill="#6dbb76")
    draw.rectangle((0, 350, size, size), fill="#4a99c9")

    for x in range(-30, size + 30, 45):
        draw.polygon([(x, 318), (x + 18, 252), (x + 36, 318)], fill="#236b3b")
        draw.rectangle((x + 15, 318, x + 21, 344), fill="#6a4327")

    for y in range(372, size, 24):
        draw.arc((60, y - 20, 452, y + 26), 8, 172, fill="#d8f3ff", width=2)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def create_secret(path: Path, size: int = 512) -> None:
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    title_font = font(72, bold=True)
    small_font = font(30, bold=True)

    draw.rectangle((52, 74, 460, 438), outline="black", width=10)
    draw.rounded_rectangle((158, 190, 354, 342), radius=24, outline="black", width=12)
    draw.arc((184, 112, 328, 254), 180, 360, fill="black", width=14)
    draw.ellipse((240, 248, 272, 280), fill="black")
    draw.rectangle((250, 276, 262, 310), fill="black")

    text = "SECRET"
    bbox = draw.textbbox((0, 0), text, font=title_font)
    draw.text(((size - (bbox[2] - bbox[0])) / 2, 356), text, fill="black", font=title_font)

    note = "LSB PAYLOAD"
    bbox = draw.textbbox((0, 0), note, font=small_font)
    draw.text(((size - (bbox[2] - bbox[0])) / 2, 94), note, fill="black", font=small_font)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> None:
    root = Path(r"D:\thesis")
    out = root / "experiments" / "inputs"
    create_landscape(out / "lsb_landscape_cover.png")
    create_secret(out / "lsb_secret_payload.png")
    print(f"Wrote LSB demo inputs to {out}")


if __name__ == "__main__":
    main()
