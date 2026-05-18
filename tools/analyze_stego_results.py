#!/usr/bin/env python
"""Analyze DiffStega and LSB outputs with CPU-friendly image metrics."""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


@dataclass
class MetricRow:
    case: str
    comparison: str
    reference: str
    candidate: str
    psnr: float
    ssim: float
    mae: float
    rmse: float


@dataclass
class ParameterSummary:
    case: str
    family: str
    value: float
    stego_psnr: float
    stego_ssim: float
    correct_psnr: float
    correct_ssim: float
    wrong_psnr: float
    wrong_ssim: float
    key_security_gap: float
    composite_score: float


def load_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if size is not None and image.size != size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return image


def image_arrays(a: Image.Image, b: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    b = b.resize(a.size, Image.Resampling.LANCZOS) if b.size != a.size else b
    return np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a - b) ** 2)
    if mse == 0:
        return float("inf")
    return 20 * math.log10(255.0 / math.sqrt(mse))


def ssim_global(a: np.ndarray, b: np.ndarray) -> float:
    # Global SSIM is enough for a lightweight undergraduate comparison table.
    a_gray = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    b_gray = 0.299 * b[:, :, 0] + 0.587 * b[:, :, 1] + 0.114 * b[:, :, 2]
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    mu_a = a_gray.mean()
    mu_b = b_gray.mean()
    var_a = a_gray.var()
    var_b = b_gray.var()
    cov = ((a_gray - mu_a) * (b_gray - mu_b)).mean()
    return ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / (
        (mu_a**2 + mu_b**2 + c1) * (var_a + var_b + c2)
    )


def compute_metrics(reference: Path, candidate: Path, case: str, comparison: str) -> MetricRow:
    ref_img = load_rgb(reference)
    cand_img = load_rgb(candidate, ref_img.size)
    ref_arr, cand_arr = image_arrays(ref_img, cand_img)
    diff = ref_arr - cand_arr
    mae = float(np.mean(np.abs(diff)))
    rmse = float(math.sqrt(np.mean(diff**2)))
    return MetricRow(
        case=case,
        comparison=comparison,
        reference=str(reference),
        candidate=str(candidate),
        psnr=psnr(ref_arr, cand_arr),
        ssim=float(ssim_global(ref_arr, cand_arr)),
        mae=mae,
        rmse=rmse,
    )


def amplified_diff(reference: Path, candidate: Path, out_path: Path, factor: int = 8) -> None:
    ref = load_rgb(reference)
    cand = load_rgb(candidate, ref.size)
    diff = ImageChops.difference(ref, cand)
    arr = np.asarray(diff, dtype=np.uint16) * factor
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(out_path)


def residual_map(image_path: Path, out_path: Path, factor: int = 6) -> None:
    image = load_rgb(image_path).convert("L")
    blurred = image.filter(ImageFilter.GaussianBlur(radius=1.2))
    diff = ImageChops.difference(image, blurred)
    arr = np.asarray(diff, dtype=np.uint16) * factor
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L").save(out_path)


def histogram(image_path: Path, out_path: Path, title: str) -> None:
    gray = Image.open(image_path).convert("L")
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
    chart.save(out_path)


def contact_sheet(items: list[tuple[str, Path]], out_path: Path) -> None:
    cell_w, cell_h = 256, 292
    sheet = Image.new("RGB", (cell_w * len(items), cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(items):
        image = load_rgb(path)
        image.thumbnail((240, 240), Image.Resampling.LANCZOS)
        x = idx * cell_w + (cell_w - image.width) // 2
        y = 34 + (240 - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text((idx * cell_w + 10, 10), label, fill=(20, 20, 20))
    sheet.save(out_path)


def find_diffstega_cases(diffstega_dir: Path) -> list[dict[str, Path | str]]:
    cases: list[dict[str, Path | str]] = []
    originals = []
    for path in diffstega_dir.rglob("*.png"):
        if not re.search(r"_(hide|rec|ref|wrg)_", path.name):
            originals.append(path)

    for original in originals:
        stem = original.stem
        case_dir = original.parent
        hide = next(case_dir.glob(f"{stem}_hide_pw_*.png"), None)
        rec_w = next(case_dir.glob(f"{stem}_rec_w_*.png"), None)
        wrongs = sorted(case_dir.glob(f"{stem}_rec_wo_*.png"))
        rec_wrong = wrongs[0] if wrongs else None
        if hide or rec_w or rec_wrong:
            case_name = original.stem
            if original.parent != diffstega_dir:
                case_name = f"{original.parent.name}_{original.stem}"
            cases.append(
                {
                    "case": case_name,
                    "secret": original,
                    "hide": hide,
                    "rec_w": rec_w,
                    "rec_wrong": rec_wrong,
                }
            )
    return cases


def write_metrics(rows: list[MetricRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case", "comparison", "reference", "candidate", "psnr", "ssim", "mae", "rmse"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case": row.case,
                    "comparison": row.comparison,
                    "reference": row.reference,
                    "candidate": row.candidate,
                    "psnr": "inf" if math.isinf(row.psnr) else f"{row.psnr:.4f}",
                    "ssim": f"{row.ssim:.6f}",
                    "mae": f"{row.mae:.4f}",
                    "rmse": f"{row.rmse:.4f}",
                }
            )


def parse_parameter_case(case: str) -> tuple[str, float] | None:
    match = re.match(r"param_(nf|es)_(\d+)_", case)
    if not match:
        return None
    family = "noise_flip_scale" if match.group(1) == "nf" else "edit_strength"
    value = int(match.group(2)) / 100.0
    return family, value


def build_parameter_summary(rows: list[MetricRow]) -> list[ParameterSummary]:
    grouped: dict[str, dict[str, MetricRow]] = {}
    for row in rows:
        if parse_parameter_case(row.case) is None:
            continue
        grouped.setdefault(row.case, {})[row.comparison] = row

    summaries: list[ParameterSummary] = []
    for case, values in grouped.items():
        parsed = parse_parameter_case(case)
        if parsed is None:
            continue
        if not {"stego", "correct recover", "wrong recover"}.issubset(values):
            continue
        family, value = parsed
        stego = values["stego"]
        correct = values["correct recover"]
        wrong = values["wrong recover"]
        key_gap = correct.ssim - wrong.ssim
        # Prefer high correct recovery, clear key separation, and avoid severe stego degradation.
        composite = correct.ssim + key_gap - max(0.0, 0.95 - stego.ssim) * 0.5
        summaries.append(
            ParameterSummary(
                case=case,
                family=family,
                value=value,
                stego_psnr=stego.psnr,
                stego_ssim=stego.ssim,
                correct_psnr=correct.psnr,
                correct_ssim=correct.ssim,
                wrong_psnr=wrong.psnr,
                wrong_ssim=wrong.ssim,
                key_security_gap=key_gap,
                composite_score=composite,
            )
        )
    return sorted(summaries, key=lambda item: (item.family, item.value, item.case))


def write_parameter_summary(summaries: list[ParameterSummary], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "family",
                "value",
                "stego_psnr",
                "stego_ssim",
                "correct_psnr",
                "correct_ssim",
                "wrong_psnr",
                "wrong_ssim",
                "key_security_gap",
                "composite_score",
            ],
        )
        writer.writeheader()
        for row in summaries:
            writer.writerow(
                {
                    "case": row.case,
                    "family": row.family,
                    "value": f"{row.value:.2f}",
                    "stego_psnr": f"{row.stego_psnr:.4f}",
                    "stego_ssim": f"{row.stego_ssim:.6f}",
                    "correct_psnr": f"{row.correct_psnr:.4f}",
                    "correct_ssim": f"{row.correct_ssim:.6f}",
                    "wrong_psnr": f"{row.wrong_psnr:.4f}",
                    "wrong_ssim": f"{row.wrong_ssim:.6f}",
                    "key_security_gap": f"{row.key_security_gap:.6f}",
                    "composite_score": f"{row.composite_score:.6f}",
                }
            )


def draw_line_chart(
    summaries: list[ParameterSummary],
    family: str,
    out_path: Path,
    title: str,
) -> None:
    items = [item for item in summaries if item.family == family]
    if not items:
        return

    width, height = 760, 440
    margin_left, margin_right = 78, 38
    margin_top, margin_bottom = 52, 70
    chart = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(chart)

    x_values = [item.value for item in items]
    series = [
        ("stego SSIM", [item.stego_ssim for item in items], (80, 120, 180)),
        ("correct SSIM", [item.correct_ssim for item in items], (40, 150, 85)),
        ("wrong SSIM", [item.wrong_ssim for item in items], (190, 85, 70)),
        ("security gap", [item.key_security_gap for item in items], (120, 90, 170)),
    ]
    y_values = [value for _, values, _ in series for value in values]
    y_min = min(y_values)
    y_max = max(y_values)
    pad = max((y_max - y_min) * 0.12, 0.01)
    y_min -= pad
    y_max += pad

    plot_x0 = margin_left
    plot_y0 = height - margin_bottom
    plot_x1 = width - margin_right
    plot_y1 = margin_top
    draw.text((margin_left, 16), title, fill=(20, 20, 20))
    draw.line((plot_x0, plot_y0, plot_x1, plot_y0), fill=(0, 0, 0))
    draw.line((plot_x0, plot_y0, plot_x0, plot_y1), fill=(0, 0, 0))

    def sx(value: float) -> int:
        if max(x_values) == min(x_values):
            return (plot_x0 + plot_x1) // 2
        return int(plot_x0 + (value - min(x_values)) / (max(x_values) - min(x_values)) * (plot_x1 - plot_x0))

    def sy(value: float) -> int:
        return int(plot_y0 - (value - y_min) / (y_max - y_min) * (plot_y0 - plot_y1))

    for idx in range(5):
        y = plot_y0 - int(idx * (plot_y0 - plot_y1) / 4)
        value = y_min + idx * (y_max - y_min) / 4
        draw.line((plot_x0, y, plot_x1, y), fill=(230, 230, 230))
        draw.text((8, y - 7), f"{value:.3f}", fill=(80, 80, 80))

    for value in x_values:
        x = sx(value)
        draw.line((x, plot_y0, x, plot_y0 + 5), fill=(0, 0, 0))
        draw.text((x - 12, plot_y0 + 10), f"{value:.2f}", fill=(50, 50, 50))

    legend_x = margin_left
    legend_y = height - 32
    for idx, (label, values, color) in enumerate(series):
        points = [(sx(x), sy(y)) for x, y in zip(x_values, values)]
        if len(points) > 1:
            draw.line(points, fill=color, width=3)
        for point in points:
            x, y = point
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
        lx = legend_x + idx * 160
        draw.line((lx, legend_y, lx + 24, legend_y), fill=color, width=3)
        draw.text((lx + 30, legend_y - 7), label, fill=(40, 40, 40))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    chart.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diffstega-dir", type=Path, default=Path("experiments/diffstega_outputs"))
    parser.add_argument("--lsb-dir", type=Path, default=Path("experiments/lsb_outputs"))
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/analysis"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[MetricRow] = []

    for case in find_diffstega_cases(args.diffstega_dir):
        name = str(case["case"])
        secret = case["secret"]
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
        if len(items) > 1:
            contact_sheet(items, args.out_dir / f"{name}_diffstega_comparison.png")

    for stego in args.lsb_dir.glob("*_lsb_stego.png"):
        prefix = stego.name[: -len("_lsb_stego.png")]
        cover = args.lsb_dir / f"{prefix}_cover.png"
        secret = args.lsb_dir / f"{prefix}_secret_resized.png"
        recovered = args.lsb_dir / f"{prefix}_lsb_recovered.png"
        if cover.exists():
            rows.append(compute_metrics(cover, stego, prefix, "lsb cover-vs-stego"))
            amplified_diff(cover, stego, args.out_dir / f"{prefix}_lsb_cover_stego_diff_x32.png", factor=32)
            residual_map(stego, args.out_dir / f"{prefix}_lsb_stego_residual.png")
            histogram(cover, args.out_dir / f"{prefix}_cover_hist.png", f"{prefix} cover histogram")
            histogram(stego, args.out_dir / f"{prefix}_lsb_stego_hist.png", f"{prefix} LSB stego histogram")
            if recovered.exists():
                items = [("cover", cover)]
                if secret.exists():
                    items.append(("secret", secret))
                items.extend([("LSB stego", stego), ("recovered secret", recovered)])
                contact_sheet(
                    items,
                    args.out_dir / f"{prefix}_lsb_comparison.png",
                )

    write_metrics(rows, args.out_dir / "metrics.csv")
    summaries = build_parameter_summary(rows)
    write_parameter_summary(summaries, args.out_dir / "parameter_summary.csv")
    draw_line_chart(summaries, "noise_flip_scale", args.out_dir / "parameter_noise_flip_scale.png",
                    "Noise Flip scale sensitivity")
    draw_line_chart(summaries, "edit_strength", args.out_dir / "parameter_edit_strength.png",
                    "Edit strength sensitivity")
    print(f"Wrote {len(rows)} metric rows and visual artifacts to {args.out_dir.resolve()}")
    print(f"Wrote {len(summaries)} parameter summary rows")


if __name__ == "__main__":
    main()
