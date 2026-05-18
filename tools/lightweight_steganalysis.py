#!/usr/bin/env python
"""Lightweight steganalysis-style statistics for thesis experiments."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FeatureRow:
    group: str
    case: str
    path: str
    lsb_one_ratio: float
    lsb_balance: float
    lsb_entropy: float
    chi_square_pair: float
    lsb_flip_rate: float
    residual_mean: float
    residual_std: float
    high_freq_energy: float
    laplacian_variance: float
    edge_density: float


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)


def to_gray(array: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)


def binary_entropy(p: float) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    return float(-(p * math.log2(p) + (1 - p) * math.log2(1 - p)))


def chi_square_pair(gray: np.ndarray) -> float:
    hist = np.bincount(gray.reshape(-1), minlength=256).astype(np.float64)
    chi = 0.0
    used = 0
    for i in range(0, 256, 2):
        pair_sum = hist[i] + hist[i + 1]
        if pair_sum <= 0:
            continue
        expected = pair_sum / 2.0
        chi += ((hist[i] - expected) ** 2 + (hist[i + 1] - expected) ** 2) / expected
        used += 1
    return float(chi / max(used, 1))


def lsb_flip_rate(gray: np.ndarray) -> float:
    bits = gray & 1
    horizontal = bits[:, 1:] ^ bits[:, :-1]
    vertical = bits[1:, :] ^ bits[:-1, :]
    return float((horizontal.mean() + vertical.mean()) / 2.0)


def features_for(path: Path, group: str, case: str) -> FeatureRow:
    rgb = load_rgb(path)
    gray = to_gray(rgb)
    lsb = (rgb & 1).astype(np.float64)
    one_ratio = float(lsb.mean())
    balance = float(abs(one_ratio - 0.5))
    entropy = binary_entropy(one_ratio)

    gray_f = gray.astype(np.float32)
    blur = cv2.GaussianBlur(gray_f, (0, 0), sigmaX=1.2)
    residual = gray_f - blur
    lap = cv2.Laplacian(gray_f, cv2.CV_32F, ksize=3)
    edges = cv2.Canny(gray, 80, 160)

    return FeatureRow(
        group=group,
        case=case,
        path=str(path),
        lsb_one_ratio=one_ratio,
        lsb_balance=balance,
        lsb_entropy=entropy,
        chi_square_pair=chi_square_pair(gray),
        lsb_flip_rate=lsb_flip_rate(gray),
        residual_mean=float(np.mean(np.abs(residual))),
        residual_std=float(np.std(residual)),
        high_freq_energy=float(np.mean(np.abs(lap))),
        laplacian_variance=float(np.var(lap)),
        edge_density=float((edges > 0).mean()),
    )


def find_secret_and_stego_cases(base_dirs: list[Path]) -> list[tuple[str, Path, Path]]:
    cases: list[tuple[str, Path, Path]] = []
    for base in base_dirs:
        if not base.exists():
            continue
        for case_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            originals = [
                p
                for p in case_dir.glob("*.png")
                if not any(tag in p.name for tag in ["_hide_", "_rec_", "_ref_", "_wrg_"])
            ]
            hides = sorted(case_dir.glob("*_hide_pw_*.png"))
            if originals and hides:
                cases.append((case_dir.name, originals[0], hides[0]))
    return cases


def collect_rows() -> list[FeatureRow]:
    rows: list[FeatureRow] = []
    lsb_dir = ROOT / "experiments" / "lsb_outputs"
    for path in sorted(lsb_dir.glob("*_cover.png")):
        case = path.name[: -len("_cover.png")]
        rows.append(features_for(path, "lsb_cover", case))
    for path in sorted(lsb_dir.glob("*_lsb_stego.png")):
        case = path.name[: -len("_lsb_stego.png")]
        rows.append(features_for(path, "lsb_stego", case))

    diff_cases = find_secret_and_stego_cases(
        [
            ROOT / "experiments" / "diffstega_outputs_hq",
            ROOT / "experiments" / "diffstega_outputs_hq_ext",
        ]
    )
    for case, secret, stego in diff_cases:
        rows.append(features_for(secret, "diffstega_secret", case))
        rows.append(features_for(stego, "diffstega_stego", case))
    return rows


def write_rows(rows: list[FeatureRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(rows[0]).keys()) if rows else [field.name for field in FeatureRow.__dataclass_fields__.values()]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in data.items():
                if isinstance(value, float):
                    data[key] = f"{value:.6f}"
            writer.writerow(data)


def group_summary(rows: list[FeatureRow]) -> list[dict[str, str]]:
    numeric = [
        "lsb_one_ratio",
        "lsb_balance",
        "lsb_entropy",
        "chi_square_pair",
        "lsb_flip_rate",
        "residual_mean",
        "residual_std",
        "high_freq_energy",
        "laplacian_variance",
        "edge_density",
    ]
    grouped: dict[str, list[FeatureRow]] = defaultdict(list)
    for row in rows:
        grouped[row.group].append(row)

    output: list[dict[str, str]] = []
    for group, items in sorted(grouped.items()):
        row: dict[str, str] = {"group": group, "count": str(len(items))}
        for field in numeric:
            values = np.asarray([getattr(item, field) for item in items], dtype=np.float64)
            row[f"{field}_mean"] = f"{values.mean():.6f}"
            row[f"{field}_std"] = f"{values.std(ddof=0):.6f}"
        output.append(row)
    return output


def write_summary(summary: list[dict[str, str]], out_path: Path) -> None:
    if not summary:
        return
    fields = list(summary[0].keys())
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)


def bar_chart(summary: list[dict[str, str]], fields: list[tuple[str, str]], out_path: Path, title: str) -> None:
    groups = [row["group"] for row in summary]
    width, height = 1180, 680
    margin_left, margin_right = 120, 40
    margin_top, margin_bottom = 86, 140
    chart = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(chart)
    title_font = font(28, bold=True)
    label_font = font(18)
    small_font = font(15)
    draw.text((margin_left, 24), title, fill=(25, 25, 25), font=title_font)

    values = {label: [float(row[f"{field}_mean"]) for row in summary] for field, label in fields}
    all_values = [v for vals in values.values() for v in vals]
    ymax = max(all_values) * 1.15 if all_values else 1.0
    if ymax <= 0:
        ymax = 1.0

    plot_x0, plot_y0 = margin_left, height - margin_bottom
    plot_x1, plot_y1 = width - margin_right, margin_top
    draw.line((plot_x0, plot_y0, plot_x1, plot_y0), fill=(0, 0, 0), width=2)
    draw.line((plot_x0, plot_y0, plot_x0, plot_y1), fill=(0, 0, 0), width=2)
    for i in range(5):
        y = plot_y0 - int(i * (plot_y0 - plot_y1) / 4)
        val = ymax * i / 4
        draw.line((plot_x0, y, plot_x1, y), fill=(228, 228, 228))
        draw.text((20, y - 10), f"{val:.3f}", fill=(80, 80, 80), font=small_font)

    colors = [(58, 112, 185), (206, 98, 72), (62, 145, 93), (142, 92, 180)]
    group_w = (plot_x1 - plot_x0) / max(len(groups), 1)
    bar_w = min(42, group_w / (len(fields) + 1))
    for gi, group in enumerate(groups):
        center = plot_x0 + group_w * gi + group_w / 2
        start = center - bar_w * len(fields) / 2
        for fi, (_, label) in enumerate(fields):
            value = values[label][gi]
            x0 = int(start + fi * bar_w)
            x1 = int(x0 + bar_w * 0.78)
            y1 = plot_y0
            y0 = int(plot_y0 - value / ymax * (plot_y0 - plot_y1))
            draw.rectangle((x0, y0, x1, y1), fill=colors[fi % len(colors)])
        draw.text((int(center - 70), plot_y0 + 18), group, fill=(45, 45, 45), font=small_font)

    legend_y = height - 64
    for fi, (_, label) in enumerate(fields):
        x = margin_left + fi * 250
        draw.rectangle((x, legend_y, x + 26, legend_y + 16), fill=colors[fi % len(colors)])
        draw.text((x + 34, legend_y - 2), label, fill=(35, 35, 35), font=label_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    chart.save(out_path)


def write_interpretation(summary: list[dict[str, str]], out_path: Path) -> None:
    by_group = {row["group"]: row for row in summary}
    lines = [
        "# 轻量隐写分析特征对比解释",
        "",
        "本实验不接入深度隐写分析器，而是使用低位统计和残差特征对 LSB 修改式隐写与 DiffStega 生成式载密图像进行机制层面的轻量对比。",
        "",
    ]
    if "lsb_cover" in by_group and "lsb_stego" in by_group:
        cover = by_group["lsb_cover"]
        stego = by_group["lsb_stego"]
        lines.extend(
            [
                "LSB 对照中，cover 与 stego 在视觉上非常接近，但最低有效位统计和残差特征仍可被单独计算。",
                f"本实验中 LSB cover 的 LSB entropy 均值为 {cover['lsb_entropy_mean']}，LSB stego 的 LSB entropy 均值为 {stego['lsb_entropy_mean']}；",
                f"LSB cover 的 chi-square pair 均值为 {cover['chi_square_pair_mean']}，LSB stego 的 chi-square pair 均值为 {stego['chi_square_pair_mean']}。",
                "",
            ]
        )
    if "diffstega_stego" in by_group:
        ds = by_group["diffstega_stego"]
        lines.extend(
            [
                "DiffStega 载密图像不是在已有 cover 上进行 LSB 嵌入，因此本实验不把传统 LSB 检测结果解释为完整安全证明。",
                f"DiffStega stego 组的 LSB entropy 均值为 {ds['lsb_entropy_mean']}，chi-square pair 均值为 {ds['chi_square_pair_mean']}，可作为与 LSB 修改式隐写的低位统计对照。",
                "论文中应表述为：DiffStega 载密生成图像未表现出传统 LSB 型最低有效位嵌入的直接修改机制，但其安全性仍需要深度隐写分析器和生成图像检测器进一步验证。",
            ]
        )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def validate(rows: list[FeatureRow]) -> None:
    for row in rows:
        for key, value in asdict(row).items():
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"Non-finite value for {row.case} {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "experiments" / "analysis_steganalysis")
    args = parser.parse_args()

    rows = collect_rows()
    if not rows:
        raise RuntimeError("No images found for lightweight steganalysis")
    validate(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = group_summary(rows)
    write_rows(rows, args.out_dir / "lightweight_steganalysis.csv")
    write_summary(summary, args.out_dir / "lightweight_steganalysis_group_summary.csv")
    bar_chart(
        summary,
        [("lsb_entropy", "LSB entropy"), ("lsb_balance", "LSB balance"), ("chi_square_pair", "Chi-square")],
        args.out_dir / "lsb_vs_diffstega_lsb_stats.png",
        "低位统计特征对比",
    )
    bar_chart(
        summary,
        [("residual_std", "Residual std"), ("high_freq_energy", "High-frequency"), ("edge_density", "Edge density")],
        args.out_dir / "lsb_vs_diffstega_residual_stats.png",
        "残差与纹理特征对比",
    )
    write_interpretation(summary, args.out_dir / "steganalysis_interpretation.md")
    print(f"Wrote {len(rows)} lightweight steganalysis rows to {args.out_dir}")
    print(f"Wrote {len(summary)} group summary rows")


if __name__ == "__main__":
    main()
