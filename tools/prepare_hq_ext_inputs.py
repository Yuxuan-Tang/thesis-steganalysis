#!/usr/bin/env python
"""Create public sample images for the HQ extension experiments."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from skimage import data


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "experiments" / "inputs_hq_ext"


def to_rgb_image(array: np.ndarray) -> Image.Image:
    if array.dtype == bool:
        array = (array.astype(np.uint8) * 255)
    elif array.max() <= 1.0:
        array = (array * 255).astype(np.uint8)
    else:
        array = array.astype(np.uint8)
    image = Image.fromarray(array)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return ImageOps.fit(image, (512, 512), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def safe_sample(name: str):
    try:
        return getattr(data, name)()
    except Exception:
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    samples: dict[str, np.ndarray | None] = {
        "sk_astronaut": safe_sample("astronaut"),
        "sk_coffee": safe_sample("coffee"),
        "sk_rocket": safe_sample("rocket"),
        "sk_cat": safe_sample("chelsea"),
        "sk_camera": safe_sample("camera"),
        "sk_horse": safe_sample("horse"),
        "sk_hubble": safe_sample("hubble_deep_field"),
        "sk_retina": safe_sample("retina"),
    }

    # Fallbacks keep the batch deterministic across skimage versions.
    if samples["sk_retina"] is None:
        samples["sk_retina"] = safe_sample("immunohistochemistry")
    if samples["sk_hubble"] is None:
        samples["sk_hubble"] = safe_sample("coins")

    written = []
    for name, array in samples.items():
        if array is None:
            continue
        out_path = OUT_DIR / f"{name}.png"
        to_rgb_image(np.asarray(array)).save(out_path)
        written.append(out_path)

    print(f"Wrote {len(written)} extension input images to {OUT_DIR}")
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
