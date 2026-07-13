"""
Shared utilities for exporting and rendering Figure 0.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from adjustText import adjust_text
from matplotlib.lines import Line2D
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


def configure_figure_style() -> None:
    """Apply the same plotting style used by the main plotting script."""
    sns.set_style("whitegrid")
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["font.size"] = 18
    plt.rcParams["axes.labelsize"] = 20
    plt.rcParams["axes.titlesize"] = 20
    plt.rcParams["xtick.labelsize"] = 18
    plt.rcParams["ytick.labelsize"] = 18
    plt.rcParams["legend.fontsize"] = 16


def default_label_data_path(base_dir: Path) -> Path:
    """Return the default editable label data path."""
    return base_dir / "data" / "figure_0_swe_bench_labels.csv"


def default_output_path(base_dir: Path) -> Path:
    """Return the default Figure 0 output path."""
    return base_dir.parent / "overleaf" / "images" / "Figure_0_SWE_Bench_Illustration.pdf"


def ensure_figure_0_label_data(base_dir: Path, output_path: Path | None = None) -> Path:
    """Reuse an existing editable CSV, or create it with default labels if missing."""
    output_path = output_path or default_label_data_path(base_dir)
    if output_path.exists():
        logger.info("Reusing existing Figure 0 label data at %s", output_path)
        return output_path
    return export_figure_0_label_data(base_dir, output_path)


def build_figure_0_rank_dataframe(base_dir: Path) -> pd.DataFrame:
    """Build the minimal label/rank dataframe used to draw Figure 0."""
    swe_bench_path = base_dir / "data" / "processed" / "cleaned" / "SWE-bench (Verified)"
    lmarena_coding_path = base_dir / "data" / "processed" / "cleaned" / "LMArena-Coding"

    swe_bench_df = pd.read_csv(swe_bench_path / "cleaned_data.csv")
    lmarena_coding_df = pd.read_csv(lmarena_coding_path / "cleaned_data.csv")

    with open(swe_bench_path / "mapping.json", "r", encoding="utf-8") as f:
        mapping = json.load(f)

    rank_pairs = []
    for swe_model_name in mapping.keys():
        swe_rows = swe_bench_df[swe_bench_df["model_name"] == swe_model_name]
        if swe_rows.empty:
            continue

        lmarena_model_name = mapping[swe_model_name]
        lmarena_rows = lmarena_coding_df[lmarena_coding_df["model_name"] == lmarena_model_name]
        if lmarena_rows.empty:
            continue

        swe_row = swe_rows.iloc[0]
        lmarena_row = lmarena_rows.iloc[0]

        rank_pairs.append(
            {
                "display_name": lmarena_model_name,
                "swe_score": float(swe_row["score"]),
                "lmarena_score": float(lmarena_row["score"]),
            }
        )

    rank_df = pd.DataFrame(rank_pairs)
    if rank_df.empty:
        raise ValueError("No overlapping mapped models were found for Figure 0.")

    rank_df = rank_df.sort_values("swe_score", ascending=False).reset_index(drop=True)
    rank_df["swe_rank"] = range(1, len(rank_df) + 1)

    rank_df = rank_df.sort_values("lmarena_score", ascending=False).reset_index(drop=True)
    rank_df["lmarena_rank"] = range(1, len(rank_df) + 1)

    rank_df = rank_df.sort_values("lmarena_rank").reset_index(drop=True)
    return rank_df[["display_name", "swe_rank", "lmarena_rank"]]


def export_figure_0_label_data(base_dir: Path, output_path: Path | None = None) -> Path:
    """Export the editable label/rank data file for Figure 0."""
    output_path = output_path or default_label_data_path(base_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rank_df = build_figure_0_rank_dataframe(base_dir)
    rank_df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Exported Figure 0 label data to %s", output_path)
    return output_path


def load_figure_0_label_data(data_path: Path) -> pd.DataFrame:
    """Load the editable label/rank data file for Figure 0."""
    rank_df = pd.read_csv(data_path)

    required_columns = {"display_name", "swe_rank", "lmarena_rank"}
    missing = required_columns - set(rank_df.columns)
    if missing:
        raise ValueError(f"Figure 0 label data is missing required columns: {sorted(missing)}")

    rank_df["display_name"] = rank_df["display_name"].fillna("").astype(str)
    rank_df["swe_rank"] = pd.to_numeric(rank_df["swe_rank"], errors="raise")
    rank_df["lmarena_rank"] = pd.to_numeric(rank_df["lmarena_rank"], errors="raise")
    return rank_df


def render_figure_0_from_file(data_path: Path, output_path: Path) -> Path:
    """Render Figure 0 from the editable label/rank data file."""
    configure_figure_style()
    rank_df = load_figure_0_label_data(data_path)
    logger.info("Rendering Figure 0 from %s with %d labeled points", data_path, len(rank_df))

    fig, ax = plt.subplots(figsize=(12, 7))

    max_rank = int(max(rank_df["swe_rank"].max(), rank_df["lmarena_rank"].max()))
    ax.plot([1, max_rank], [1, max_rank], "r--", linewidth=2, zorder=1)

    ax.scatter(
        rank_df["swe_rank"],
        rank_df["lmarena_rank"],
        alpha=0.7,
        s=100,
        edgecolors="black",
        linewidth=1.5,
        zorder=5,
    )

    texts = []
    for _, row in rank_df.iterrows():
        texts.append(
            ax.annotate(
                row["display_name"],
                (row["swe_rank"], row["lmarena_rank"]),
                fontsize=16,
                alpha=0.8,
                zorder=4,
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    alpha=0.7,
                    edgecolor="none",
                ),
            )
        )

    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="->", color="gray", lw=0.5))

    spearman_rho, _ = spearmanr(rank_df["swe_rank"], rank_df["lmarena_rank"])
    ax.text(
        0.02,
        0.98,
        f"Spearman ρ = {spearman_rho:.3f}",
        fontsize=18,
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor="gray"),
        zorder=3,
    )

    legend_elements = [Line2D([0], [0], color="red", linestyle="--", linewidth=2, label="y=x")]
    legend = ax.legend(
        legend_elements,
        ["y=x"],
        loc="lower right",
        fontsize=18,
        framealpha=0.9,
        fancybox=True,
        shadow=False,
    )
    legend.set_zorder(3)

    ax.set_xlabel("Rank in SWE-bench (Verified) (Weak → Strong)", fontsize=20)
    ax.set_ylabel("Rank in LMArena-Coding (Weak → Strong)", fontsize=20)

    ax.set_xlim(max_rank + 0.5, 0.5)
    ax.set_ylim(max_rank + 0.5, 0.5)

    tick_positions = list(range(1, max_rank + 1, 5))
    ax.set_xticks(tick_positions)
    ax.set_yticks(tick_positions)
    ax.set_xticklabels(tick_positions, fontsize=18)
    ax.set_yticklabels(tick_positions, fontsize=18)

    ax.grid(True, color="lightgray", linestyle="-", linewidth=0.5, alpha=0.5, zorder=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf", bbox_inches="tight")
    plt.close()
    logger.info("Saved Figure 0 to %s", output_path)
    return output_path
