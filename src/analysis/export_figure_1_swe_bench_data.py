from __future__ import annotations

import argparse
from pathlib import Path

from figure_1_swe_bench import default_label_data_path, export_figure_1_label_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Export editable label/rank data for Figure 1.")
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional custom path for the exported CSV file.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent.parent
    output_path = args.output_path or default_label_data_path(base_dir)
    export_figure_1_label_data(base_dir, output_path)
    print(f"Exported Figure 1 label data to: {output_path}")


if __name__ == "__main__":
    main()
