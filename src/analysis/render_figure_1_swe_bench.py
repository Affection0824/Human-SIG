from __future__ import annotations

import argparse
from pathlib import Path

from figure_1_swe_bench import default_label_data_path, default_output_path, render_figure_1_from_file


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
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = args.data_path or default_label_data_path(base_dir)
    output_path = args.output_path or default_output_path(base_dir)
    render_figure_1_from_file(data_path, output_path)
    print(f"Rendered Figure 1 to: {output_path}")


if __name__ == "__main__":
    main()
