"""
Apply Holm-Bonferroni Correction to Hypothesis Test Results

Purpose:
    This script applies Holm-Bonferroni correction for multiple comparisons to the
    raw p-values from hypothesis tests. This correction controls the family-wise
    error rate (FWER) while being less conservative than standard Bonferroni.

Input:
    - hypothesis_test_results.json: Raw p-values from Step 4.3

Output:
    - statistical_significance_report.json: Corrected p-values and significance flags
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import logging
import sys

sys.path.insert(0, str(Path(__file__).parent))

from stats_utils import holm_bonferroni_correction

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_hypothesis_results(results_path: Path) -> Dict:
    """Load hypothesis test results."""
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_conclusion(result: Dict, hypothesis_key: str) -> str:
    """
    Generate textual conclusion for a hypothesis test result.
    
    Args:
        result: Result dictionary with p-values and effect sizes
        hypothesis_key: Hypothesis identifier (e.g., "H1_spearman_rho")
        
    Returns:
        Textual conclusion string
    """
    p_raw = result.get('p_raw', np.nan)
    p_corrected = result.get('p_corrected', np.nan)
    significant = result.get(
        'significant_strict',
        result.get('is_significant', False),
    )
    effect_size = result.get('effect_size', np.nan)
    effect_type = result.get('effect_size_type', 'unknown')
    
    if pd.isna(p_raw):
        return "Insufficient data for statistical testing."
    
    if significant:
        conclusion = f"Statistically significant after correction (p_corrected = {p_corrected:.4f}). "
    else:
        conclusion = f"Not statistically significant after correction (p_corrected = {p_corrected:.4f}). "
    
    if pd.notna(effect_size):
        if effect_type == 'beta_coefficient':
            conclusion += f"Effect size (β) = {effect_size:.3f}."
        elif effect_type in ['spearman_rho', 'pearson_r']:
            conclusion += f"Correlation (r) = {effect_size:.3f}."
        elif effect_type == 'median_difference':
            conclusion += f"Median difference = {effect_size:.3f}."
        else:
            conclusion += f"Effect size = {effect_size:.3f}."
    
    return conclusion


def apply_correction(hypothesis_results: Dict) -> Dict:
    """
    Apply Holm-Bonferroni correction to all p-values.
    
    Args:
        hypothesis_results: Dictionary of hypothesis test results
        
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    # Extract all p-values
    p_values_dict = {}
    full_results = {}
    
    for key, result in hypothesis_results.items():
        p_raw = result.get('p_raw', np.nan)
        if pd.notna(p_raw):
            p_values_dict[key] = p_raw
        full_results[key] = result
    
    # Apply Holm-Bonferroni correction
    logger.info(f"Applying Holm-Bonferroni correction to {len(p_values_dict)} tests...")
    corrected_results = holm_bonferroni_correction(p_values_dict, alpha=0.05)
    
    # Merge corrected p-values back into full results
    output_results = {}
    
    for key, result in full_results.items():
        if key in corrected_results:
            # Merge correction results
            output_results[key] = {
                **result,
                'p_raw': corrected_results[key]['p_raw'],
                'p_corrected': corrected_results[key]['p_corrected'],
                'significant_strict': corrected_results[key]['is_significant']
            }
        else:
            # No p-value (e.g., RBO without p-value)
            output_results[key] = {
                **result,
                'p_raw': result.get('p_raw', np.nan),
                'p_corrected': np.nan,
                'significant_strict': False
            }
        
        # Add conclusion
        output_results[key]['conclusion'] = format_conclusion(output_results[key], key)
    
    return output_results


def main():
    """Main execution function."""
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "results" / "hypothesis_test_results.json"
    output_path = base_dir / "results" / "statistical_significance_report.json"
    
    # Load results
    logger.info(f"Loading hypothesis test results from {input_path}...")
    hypothesis_results = load_hypothesis_results(input_path)
    
    # Apply correction
    corrected_results = apply_correction(hypothesis_results)
    
    # Format output according to schema
    output = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "description": "Statistical significance report for all hypotheses after Holm-Bonferroni correction",
        **corrected_results
    }
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Saved corrected results to {output_path}")
    
    # Print summary
    logger.info("\n=== Correction Summary ===")
    significant_count = sum(1 for r in corrected_results.values() if r.get('significant_strict', False))
    total_count = len(corrected_results)
    logger.info(f"Total tests: {total_count}")
    logger.info(f"Significant after correction: {significant_count}")
    logger.info(f"Not significant: {total_count - significant_count}")


if __name__ == "__main__":
    main()

