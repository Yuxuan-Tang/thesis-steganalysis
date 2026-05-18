#!/usr/bin/env python
"""Combine original and extension HQ analyses for thesis tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def classify(case: str) -> str:
    if case.startswith("hq_ext_sk_"):
        return "extended_sample"
    if case.startswith("hq_ext_pw_"):
        return "key_robustness"
    return "original_hq"


def case_label(case: str) -> str:
    if case.startswith("hq_ext_sk_"):
        label = case.replace("hq_ext_sk_", "")
        if "_sk_" in label:
            left, right = label.split("_sk_", 1)
            if left == right:
                return left
        parts = label.split("_")
        if len(parts) % 2 == 0:
            half = len(parts) // 2
            if parts[:half] == parts[half:]:
                return "_".join(parts[:half])
        return label
    if case.startswith("hq_ext_pw_"):
        return case.replace("hq_ext_pw_", "")
    return case


def metric_summary(metrics: list[dict[str, str]], family: str) -> list[dict[str, str]]:
    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in metrics:
        if classify(row["case"]) != family:
            continue
        grouped.setdefault(row["case"], {})[row["comparison"]] = row

    output = []
    for case, values in sorted(grouped.items()):
        stego = values.get("stego")
        correct = values.get("correct recover")
        wrong = values.get("wrong recover")
        if not (stego and correct and wrong):
            continue
        output.append(
            {
                "case": case,
                "label": case_label(case),
                "stego_psnr": stego["psnr"],
                "stego_ssim": stego["ssim"],
                "correct_psnr": correct["psnr"],
                "correct_ssim": correct["ssim"],
                "wrong_psnr": wrong["psnr"],
                "wrong_ssim": wrong["ssim"],
                "key_security_gap": f"{float(correct['ssim']) - float(wrong['ssim']):.6f}",
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-analysis", type=Path, default=ROOT / "experiments" / "analysis_hq")
    parser.add_argument("--ext-analysis", type=Path, default=ROOT / "experiments" / "analysis_hq_ext")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "experiments" / "analysis_hq_combined")
    args = parser.parse_args()

    old_metrics = read_csv(args.old_analysis / "hq_metrics.csv")
    ext_metrics = read_csv(args.ext_analysis / "hq_metrics.csv")
    old_three = read_csv(args.old_analysis / "three_objective_summary.csv")
    ext_three = read_csv(args.ext_analysis / "three_objective_summary.csv")

    metrics = old_metrics + ext_metrics
    three = old_three + ext_three
    write_csv(metrics, args.out_dir / "combined_hq_metrics.csv")
    write_csv(three, args.out_dir / "combined_three_objective_summary.csv")
    write_csv(metric_summary(metrics, "extended_sample"), args.out_dir / "extended_sample_summary.csv")
    write_csv(metric_summary(metrics, "key_robustness"), args.out_dir / "key_robustness_summary.csv")
    print(f"Wrote combined HQ analysis to {args.out_dir}")
    print(f"combined metric rows: {len(metrics)}")
    print(f"combined three-objective rows: {len(three)}")


if __name__ == "__main__":
    main()
