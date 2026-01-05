"""
Multiple Comparison Correction Module

Purpose:
    Apply Holm-Bonferroni correction to raw p-values from hypothesis tests to control
    family-wise error rate (FWER) in multiple comparisons.

Input:
    - Hypothesis test results: Human-SIG/results/hypothesis_test_results.json

Output:
    - Statistical significance report: Human-SIG/results/statistical_significance_report.json
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.stats_utils import holm_bonferroni_correction


def extract_pvalues_from_results(results: Dict) -> Dict[str, float]:
    """
    Extract all p-values from hypothesis test results and create a flat dictionary.
    
    Returns:
        Dictionary mapping hypothesis keys to raw p-values
    """
    p_values = {}
    
    # H6/H5: Robust Regression (Difficulty + CV)
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H6_H5_{metric}'
        if key in results:
            # Beta1 (Difficulty)
            p_values[f'H6_Difficulty_Beta1_{metric.capitalize()}'] = results[key]['beta1_pvalue']
            # Beta2 (CV)
            p_values[f'H5_Variance_Beta2_{metric.capitalize()}'] = results[key]['beta2_pvalue']
    
    # H5: Task Type Interaction
    if 'H5_TaskType_Interaction' in results:
        h5_result = results['H5_TaskType_Interaction']
        for task_type in ['MCQ', 'Generation', 'Agentic']:
            if task_type in h5_result:
                # For H5 task type interaction, we report the correlation p-values
                # Note: These are correlations between CV and Spearman rho for each task type
                # We'll use Spearman metric name for consistency
                task_key = task_type.lower()
                p_values[f'H5_Variance_{task_type}_Spearman'] = h5_result[task_type]['p_value']
    
    # H4: Recency
    if 'H4_Recency' in results:
        h4_result = results['H4_Recency']
        for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
            if metric in h4_result:
                metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
                p_values[f'H4_Recency_{metric_name}'] = h4_result[metric]['p_value']
    
    # H3: Complexity
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H3_Complexity_{metric}'
        if key in results:
            metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
            p_values[f'H3_Complexity_{metric_name}'] = results[key]['p_value']
    
    # H2: Scale
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H2_Scale_{metric}'
        if key in results:
            metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
            p_values[f'H2_Scale_{metric_name}'] = results[key]['p_value']
    
    # H1: Task Type
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H1_TaskType_{metric}'
        if key in results:
            metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
            p_values[f'H1_TaskType_{metric_name}'] = results[key]['p_value']
    
    return p_values


def extract_effect_sizes_from_results(results: Dict) -> Dict[str, Dict]:
    """
    Extract effect sizes, confidence intervals, and other metadata from results.
    
    Returns:
        Dictionary mapping hypothesis keys to metadata dictionaries
    """
    effect_data = {}
    
    # H6/H5: Robust Regression
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H6_H5_{metric}'
        metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
        
        if key in results:
            # Beta1 (Difficulty)
            h6_key = f'H6_Difficulty_Beta1_{metric_name}'
            effect_data[h6_key] = {
                'effect_size': results[key]['beta1_difficulty'],
                'effect_size_type': 'beta_coefficient',
                'ci_lower': results[key]['beta1_ci_lower'],
                'ci_upper': results[key]['beta1_ci_upper'],
                'sample_size': results[key]['n_samples']
            }
            
            # Beta2 (CV)
            h5_key = f'H5_Variance_Beta2_{metric_name}'
            effect_data[h5_key] = {
                'effect_size': results[key]['beta2_cv'],
                'effect_size_type': 'beta_coefficient',
                'ci_lower': results[key]['beta2_ci_lower'],
                'ci_upper': results[key]['beta2_ci_upper'],
                'sample_size': results[key]['n_samples']
            }
    
    # H5: Task Type Interaction
    if 'H5_TaskType_Interaction' in results:
        h5_result = results['H5_TaskType_Interaction']
        for task_type in ['MCQ', 'Generation', 'Agentic']:
            if task_type in h5_result:
                h5_key = f'H5_Variance_{task_type}_Spearman'
                effect_data[h5_key] = {
                    'effect_size': h5_result[task_type]['correlation_coefficient'],
                    'effect_size_type': 'spearman_rho',
                    'ci_lower': h5_result[task_type]['ci_lower'],
                    'ci_upper': h5_result[task_type]['ci_upper'],
                    'sample_size': h5_result[task_type]['sample_size']
                }
    
    # H4: Recency
    if 'H4_Recency' in results:
        h4_result = results['H4_Recency']
        for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
            if metric in h4_result:
                metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
                h4_key = f'H4_Recency_{metric_name}'
                effect_data[h4_key] = {
                    'effect_size': h4_result[metric]['correlation_coefficient'],
                    'effect_size_type': 'spearman_rho' if metric == 'spearman_rho' else ('kendall_tau' if metric == 'kendall_tau' else 'pearson_r'),
                    'ci_lower': h4_result[metric]['ci_lower'] if 'ci_lower' in h4_result[metric] else None,
                    'ci_upper': h4_result[metric]['ci_upper'] if 'ci_upper' in h4_result[metric] else None
                }
    
    # H3: Complexity
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H3_Complexity_{metric}'
        metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
        
        if key in results:
            h3_key = f'H3_Complexity_{metric_name}'
            effect_data[h3_key] = {
                'effect_size': results[key]['test_statistic'],
                'effect_size_type': 'spearman_rho',  # Kruskal-Wallis test statistic
                'ci_lower': None,
                'ci_upper': None
            }
    
    # H2: Scale
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H2_Scale_{metric}'
        metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
        
        if key in results:
            h2_key = f'H2_Scale_{metric_name}'
            effect_data[h2_key] = {
                'effect_size': results[key]['correlation_coefficient'],
                'effect_size_type': 'pearson_r',
                'ci_lower': None,
                'ci_upper': None,
                'sample_size': results[key]['n_samples']
            }
    
    # H1: Task Type
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        key = f'H1_TaskType_{metric}'
        metric_name = 'Spearman' if metric == 'spearman_rho' else ('Kendall' if metric == 'kendall_tau' else 'RBO')
        
        if key in results:
            h1_key = f'H1_TaskType_{metric_name}'
            if 'is_descriptive_only' in results[key] and results[key]['is_descriptive_only']:
                effect_data[h1_key] = {
                    'effect_size': results[key]['median_difference'],
                    'effect_size_type': 'median_difference',
                    'ci_lower': results[key]['ci_lower'] if 'ci_lower' in results[key] else None,
                    'ci_upper': results[key]['ci_upper'] if 'ci_upper' in results[key] else None,
                    'sample_size': results[key]['n_group_a'] + results[key]['n_group_b'],
                    'is_descriptive_only': True
                }
            else:
                effect_data[h1_key] = {
                    'effect_size': results[key]['effect_size'] if 'effect_size' in results[key] else results[key]['median_difference'],
                    'effect_size_type': 'median_difference',
                    'ci_lower': results[key]['ci_lower'] if 'ci_lower' in results[key] else None,
                    'ci_upper': results[key]['ci_upper'] if 'ci_upper' in results[key] else None,
                    'sample_size': results[key]['n_group_a'] + results[key]['n_group_b'],
                    'is_descriptive_only': False
                }
    
    return effect_data


def generate_conclusion(hypothesis_key: str, p_raw: float, p_corrected: float, 
                        significant: bool, effect_size: float, effect_size_type: str) -> str:
    """
    Generate a textual conclusion for a hypothesis test result.
    
    Args:
        hypothesis_key: Key identifying the hypothesis (e.g., "H1_TaskType_Spearman")
        p_raw: Raw p-value
        p_corrected: Corrected p-value
        significant: Whether the result is significant after correction
        effect_size: Effect size value
        effect_size_type: Type of effect size
    
    Returns:
        Textual conclusion string
    """
    if np.isnan(p_raw) or np.isnan(p_corrected):
        return "P-value is undefined (descriptive only or insufficient data)."
    
    if significant:
        significance_text = "is statistically significant"
    else:
        significance_text = "is not statistically significant"
    
    if effect_size_type == 'beta_coefficient':
        effect_text = f"coefficient = {effect_size:.4f}"
    elif effect_size_type == 'spearman_rho' or effect_size_type == 'kendall_tau':
        effect_text = f"correlation = {effect_size:.4f}"
    elif effect_size_type == 'pearson_r':
        effect_text = f"correlation = {effect_size:.4f}"
    elif effect_size_type == 'median_difference':
        effect_text = f"median difference = {effect_size:.4f}"
    else:
        effect_text = f"effect size = {effect_size:.4f}"
    
    conclusion = (f"Hypothesis {hypothesis_key} {significance_text} after Holm-Bonferroni correction "
                 f"(p_raw = {p_raw:.4f}, p_corrected = {p_corrected:.4f}). "
                 f"Effect size: {effect_text}.")
    
    return conclusion


def apply_correction_and_generate_report(
    results_path: Path,
    output_path: Path
) -> None:
    """
    Apply Holm-Bonferroni correction and generate statistical significance report.
    
    Args:
        results_path: Path to hypothesis_test_results.json
        output_path: Path to output statistical_significance_report.json
    """
    # Load results
    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Extract p-values
    p_values = extract_pvalues_from_results(results)
    
    # Filter out NaN p-values for correction (but keep them in final report)
    p_values_for_correction = {k: v for k, v in p_values.items() if not np.isnan(v)}
    
    # Apply Holm-Bonferroni correction
    corrected_results = holm_bonferroni_correction(p_values_for_correction)
    
    # Extract effect sizes
    effect_data = extract_effect_sizes_from_results(results)
    
    # Build final report
    report = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "description": "Statistical significance report for all hypotheses after Holm-Bonferroni correction"
    }
    
    report_results = {}
    
    # Process all hypotheses
    for hyp_key in p_values.keys():
        p_raw = p_values[hyp_key]
        
        if hyp_key in corrected_results:
            p_corrected = corrected_results[hyp_key]['p_corrected']
            significant = corrected_results[hyp_key]['is_significant']
        else:
            # NaN p-value
            p_corrected = np.nan
            significant = False
        
        # Get effect size data
        if hyp_key in effect_data:
            effect_info = effect_data[hyp_key]
        else:
            effect_info = {
                'effect_size': np.nan,
                'effect_size_type': 'unknown',
                'ci_lower': None,
                'ci_upper': None
            }
        
        # Generate conclusion
        conclusion = generate_conclusion(
            hyp_key, p_raw, p_corrected, significant,
            effect_info['effect_size'], effect_info['effect_size_type']
        )
        
        # Build entry
        entry = {
            'p_raw': float(p_raw) if not np.isnan(p_raw) else None,
            'p_corrected': float(p_corrected) if not np.isnan(p_corrected) else None,
            'significant_strict': bool(significant),
            'effect_size': float(effect_info['effect_size']) if not np.isnan(effect_info['effect_size']) else None,
            'effect_size_type': effect_info['effect_size_type'],
            'conclusion': conclusion
        }
        
        # Add optional fields
        if 'ci_lower' in effect_info and effect_info['ci_lower'] is not None:
            entry['ci_lower'] = float(effect_info['ci_lower']) if not np.isnan(effect_info['ci_lower']) else None
        if 'ci_upper' in effect_info and effect_info['ci_upper'] is not None:
            entry['ci_upper'] = float(effect_info['ci_upper']) if not np.isnan(effect_info['ci_upper']) else None
        if 'sample_size' in effect_info:
            entry['sample_size'] = int(effect_info['sample_size'])
        if 'is_descriptive_only' in effect_info:
            entry['is_descriptive_only'] = bool(effect_info['is_descriptive_only'])
        
        report_results[hyp_key] = entry
    
    report['results'] = report_results
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Statistical significance report saved to {output_path}")
    print(f"Total hypotheses tested: {len(p_values)}")
    print(f"Significant after correction: {sum(1 for k, v in report_results.items() if v['significant_strict'])}")


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    results_path = base_dir / "results" / "hypothesis_test_results.json"
    output_path = base_dir / "results" / "statistical_significance_report.json"
    
    apply_correction_and_generate_report(results_path, output_path)

