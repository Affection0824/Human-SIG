from __future__ import annotations

import argparse
import csv
from pathlib import Path

from figure_1_swe_bench import default_label_data_path, default_output_path, render_figure_1_from_file


def load_stored_swe_bench_spearman(analysis_data_path: Path) -> float:
    """Load the authoritative Figure 1 coefficient from main analysis output."""
    with analysis_data_path.open("r", encoding="utf-8", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("benchmark_id") == "SWE-bench (Verified)"
        ]
    if len(rows) != 1:
        raise ValueError(
            "Expected exactly one SWE-bench (Verified) row in "
            f"{analysis_data_path}"
        )
    value = rows[0].get("spearman_rho", "")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid stored SWE-bench Spearman coefficient: {value!r}"
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Figure 1 from an editable label/rank CSV.")
    parser.add_argument(
        "--data-path",
        type=Path,
        help="Optional custom path for the Figure 1 label CSV file.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional custom path for the generated Figure 1 PDF.",
    )
    parser.add_argument(
        "--analysis-data-path",
        type=Path,
        help="Optional path to the main analysis_ready_data.csv result.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = args.data_path or default_label_data_path(base_dir)
    output_path = args.output_path or default_output_path(base_dir)
    analysis_data_path = (
        args.analysis_data_path
        or base_dir / "results" / "analysis_ready_data.csv"
    )
    spearman_rho = load_stored_swe_bench_spearman(analysis_data_path)
    render_figure_1_from_file(data_path, output_path, spearman_rho)
    print(f"Rendered Figure 1 to: {output_path}")


if __name__ == "__main__":
    main()
