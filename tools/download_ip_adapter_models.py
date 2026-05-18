#!/usr/bin/env python
"""Download the IP-Adapter files required by DiffStega into the expected layout."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache" / "huggingface" / "hub"
TARGET = ROOT / "DiffStega" / "pretrained_models"

FILES = [
    ("models/ip-adapter-plus_sd15.bin", TARGET / "ip-adapter-plus_sd15.bin"),
    ("models/ip-adapter-plus-face_sd15.bin", TARGET / "ip-adapter-plus-face_sd15.bin"),
    ("models/image_encoder/pytorch_model.bin", TARGET / "image_encoder_for_ip_adapter" / "pytorch_model.bin"),
    ("models/image_encoder/config.json", TARGET / "image_encoder_for_ip_adapter" / "config.json"),
]


def main() -> None:
    os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE_DIR))
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "image_encoder_for_ip_adapter").mkdir(parents=True, exist_ok=True)

    for repo_file, dest in FILES:
        print(f"Downloading {repo_file} ...")
        source = Path(
            hf_hub_download(
                repo_id="h94/IP-Adapter",
                filename=repo_file,
                cache_dir=str(CACHE_DIR),
                resume_download=True,
            )
        )
        if not dest.exists() or source.stat().st_size != dest.stat().st_size:
            shutil.copy2(source, dest)
        print(f"  -> {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
