#!/usr/bin/env python
"""Analyze high-quality DiffStega experiments with three-objective metrics."""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from analyze_stego_results import (
    MetricRow,
    amplified_diff,
    compute_metrics,
    contact_sheet,
    find_diffstega_cases,
    histogram,
    residual_map,
    write_metrics,
)


@dataclass
class ThreeObjectiveRow:
    case: str
    family: str
    value: str
    stego_ssim: float
    correct_ssim: float
    wrong_ssim: float
    key_security_gap: float
    edge_leakage: float
    semantic_leakage: float
    three_objective_score: float


def load_gray(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    image = Image.open(path).convert("L")
    if size is not None and image.size != size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return image


def edge_array(path: Path, size: tuple[int, int]) -> np.ndarray:
    image = load_gray(path, size)
    image = ImageOps.autocontrast(image.filter(ImageFilter.FIND_EDGES))
    return np.asarray(image, dtype=np.float64).reshape(-1) / 255.0


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def chart_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def edge_leakage(secret: Path, stego: Path) -> float:
    size = Image.open(secret).size
    return cosine_similarity(edge_array(secret, size), edge_array(stego, size))


def parse_case_family(case: str) -> tuple[str, str]:
    patterns = [
        (r"^hq_ext_sk_([a-z_]+)_", "extended_sample"),
        (r"^hq_ext_pw_([a-z]+_\d+)_", "key_robustness"),
        (r"^hq_calib_steps_(\d+)_", "steps"),
        (r"^hq_param_nf_(\d+)_", "noise_flip_scale"),
        (r"^hq_param_es_(\d+)_", "edit_strength"),
        (r"^hq_prompt_([a-z]+)_", "prompt"),
        (r"^hq_core_([a-z_]+)_", "core"),
    ]
    for pattern, family in patterns:
        match = re.match(pattern, case)
        if match:
            value = match.group(1)
            if family == "noise_flip_scale" or family == "edit_strength":
                value = f"{int(value) / 100:.2f}"
            return family, value
    return "other", ""


def group_metrics(rows: list[MetricRow]) -> dict[str, dict[str, MetricRow]]:
    grouped: dict[str, dict[str, MetricRow]] = {}
    for row in rows:
        grouped.setdefault(row.case, {})[row.comparison] = row
    return grouped


def build_three_objective_rows(rows: list[MetricRow], case_paths: dict[str, tuple[Path, Path]]) -> list[ThreeObjectiveRow]:
    grouped = group_metrics(rows)
    output: list[ThreeObjectiveRow] = []
    for case, values in grouped.items():
        if not {"stego", "correct recover", "wrong recover"}.issubset(values):
            continue
        if case not in case_paths:
            continue
        family, value = parse_case_family(case)
        stego = values["stego"]
        correct = values["correct recover"]
        wrong = values["wrong recover"]
        edge = edge_leakage(*case_paths[case])
        semantic = 0.6 * stego.ssim + 0.4 * edge
        key_gap = correct.ssim - wrong.ssim
        # Higher recovery and key separation are good; higher leakage is bad.
        score = correct.ssim + key_gap - 0.35 * semantic
        output.append(
            ThreeObjectiveRow(
                case=case,
                family=family,
                value=value,
                stego_ssim=stego.ssim,
                correct_ssim=correct.ssim,
                wrong_ssim=wrong.ssim,
                key_security_gap=key_gap,
                edge_leakage=edge,
                semantic_leakage=semantic,
                three_objective_score=score,
            )
        )
    return sorted(output, key=lambda item: (item.family, item.value, item.case))


def write_three_objective(rows: list[ThreeObjectiveRow], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "family",
                "value",
                "stego_ssim",
                "correct_ssim",
                "wrong_ssim",
                "key_security_gap",
                "edge_leakage",
                "semantic_leakage",
                "three_objective_score",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case": row.case,
                    "family": row.family,
                    "value": row.value,
                    "stego_ssim": f"{row.stego_ssim:.6f}",
                    "correct_ssim": f"{row.correct_ssim:.6f}",
                    "wrong_ssim": f"{row.wrong_ssim:.6f}",
                    "key_security_gap": f"{row.key_security_gap:.6f}",
                    "edge_leakage": f"{row.edge_leakage:.6f}",
                    "semantic_leakage": f"{row.semantic_leakage:.6f}",
                    "three_objective_score": f"{row.three_objective_score:.6f}",
                }
            )


def write_semantic_leakage(rows: list[ThreeObjectiveRow], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case", "family", "value", "stego_ssim", "edge_leakage", "semantic_leakage"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case": row.case,
                    "family": row.family,
                    "value": row.value,
                    "stego_ssim": f"{row.stego_ssim:.6f}",
                    "edge_leakage": f"{row.edge_leakage:.6f}",
                    "semantic_leakage": f"{row.semantic_leakage:.6f}",
                }
            )


def draw_family_chart(rows: list[ThreeObjectiveRow], family: str, out_path: Path, title: str) -> None:
    items = [row for row in rows if row.family == family]
    if not items:
        return
    width, height = 860, 460
    margin_left, margin_right = 78, 44
    margin_top, margin_bottom = 54, 82
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = chart_font(24, bold=True)
    tick_font = chart_font(15)
    legend_font = chart_font(16)

    labels = [row.value for row in items]
    x_values = list(range(len(items)))
    series = [
        ("correct SSIM", [row.correct_ssim for row in items], (45, 135, 80)),
        ("key gap", [row.key_security_gap for row in items], (130, 90, 180)),
        ("semantic leakage", [row.semantic_leakage for row in items], (190, 85, 70)),
        ("score", [row.three_objective_score for row in items], (60, 110, 180)),
    ]
    y_values = [value for _, values, _ in series for value in values]
    y_min, y_max = min(y_values), max(y_values)
    pad = max((y_max - y_min) * 0.12, 0.01)
    y_min -= pad
    y_max += pad

    plot_x0, plot_y0 = margin_left, height - margin_bottom
    plot_x1, plot_y1 = width - margin_right, margin_top
    draw.text((margin_left, 16), title, fill=(20, 20, 20), font=title_font)
    draw.line((plot_x0, plot_y0, plot_x1, plot_y0), fill=(0, 0, 0))
    draw.line((plot_x0, plot_y0, plot_x0, plot_y1), fill=(0, 0, 0))

    def sx(index: int) -> int:
        if len(x_values) == 1:
            return (plot_x0 + plot_x1) // 2
        return int(plot_x0 + index / (len(x_values) - 1) * (plot_x1 - plot_x0))

    def sy(value: float) -> int:
        return int(plot_y0 - (value - y_min) / (y_max - y_min) * (plot_y0 - plot_y1))

    for tick in range(5):
        y = plot_y0 - int(tick * (plot_y0 - plot_y1) / 4)
        value = y_min + tick * (y_max - y_min) / 4
        draw.line((plot_x0, y, plot_x1, y), fill=(230, 230, 230))
        draw.text((8, y - 7), f"{value:.3f}", fill=(80, 80, 80), font=tick_font)

    for index, label in enumerate(labels):
        x = sx(index)
        draw.line((x, plot_y0, x, plot_y0 + 5), fill=(0, 0, 0))
        draw.text((x - 28, plot_y0 + 12), label, fill=(50, 50, 50), font=tick_font)

    for label, values, color in series:
        points = [(sx(index), sy(value)) for index, value in enumerate(values)]
        if len(points) > 1:
            draw.line(points, fill=color, width=3)
        for x, y in points:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)

    legend_y = height - 34
    for index, (label, _, color) in enumerate(series):
        x = margin_left + index * 190
        draw.line((x, legend_y, x + 24, legend_y), fill=color, width=3)
        draw.text((x + 30, legend_y - 7), label, fill=(40, 40, 40), font=legend_font)

    image.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diffstega-dir", type=Path, default=Path("experiments/diffstega_outputs_hq"))
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/analysis_hq"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[MetricRow] = []
    case_paths: dict[str, tuple[Path, Path]] = {}

    for case in find_diffstega_cases(args.diffstega_dir):
        name = str(case["case"])
        secret = case["secret"]
        hide = case["hide"]
        assert isinstance(secret, Path)
        items: list[tuple[str, Path]] = [("secret", secret)]
        for key, label in [("hide", "stego"), ("rec_w", "correct recover"), ("rec_wrong", "wrong recover")]:
            path = case[key]
            if isinstance(path, Path):
                rows.append(compute_metrics(secret, path, name, label))
                amplified_diff(secret, path, args.out_dir / f"{name}_{key}_diff_x8.png")
                residual_map(path, args.out_dir / f"{name}_{key}_residual.png")
                histogram(path, args.out_dir / f"{name}_{key}_hist.png", f"{name} {label} histogram")
                items.append((label, path))
        if isinstance(hide, Path):
            case_paths[name] = (secret, hide)
        if len(items) > 1:
            contact_sheet(items, args.out_dir / f"{name}_comparison.png")

    write_metrics(rows, args.out_dir / "hq_metrics.csv")
    three_rows = build_three_objective_rows(rows, case_paths)
    write_three_objective(three_rows, args.out_dir / "three_objective_summary.csv")
    write_semantic_leakage(three_rows, args.out_dir / "semantic_leakage_summary.csv")
    draw_family_chart(three_rows, "steps", args.out_dir / "hq_steps_three_objective.png", "采样步数三目标对比")
    draw_family_chart(three_rows, "noise_flip_scale", args.out_dir / "hq_noise_flip_three_objective.png", "Noise Flip 参数三目标对比")
    draw_family_chart(three_rows, "edit_strength", args.out_dir / "hq_edit_strength_three_objective.png", "Edit Strength 参数三目标对比")
    draw_family_chart(three_rows, "prompt", args.out_dir / "hq_prompt_three_objective.png", "Prompt 类型三目标对比")

    print(f"Wrote {len(rows)} HQ metric rows to {args.out_dir.resolve()}")
    print(f"Wrote {len(three_rows)} three-objective rows")


if __name__ == "__main__":
    main()
