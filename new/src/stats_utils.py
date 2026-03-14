"""
Advanced Statistical Utility Functions for Small-N Analysis

Purpose:
    This module provides rigorous statistical functions specifically designed for small sample
    size analysis (N=28 benchmarks). The methods implemented here are appropriate for small-N
    datasets where standard asymptotic approximations may not hold.

Functions included:
    - calculate_rbo: Rank-Biased Overlap
    - bootstrap_ci: Bootstrap resampling for confidence intervals
    - calculate_spearman_with_pvalue: Spearman correlation with permutation test for small N
    - calculate_kendall_with_pvalue: Kendall correlation with permutation test for small N
"""

import numpy as np
from scipy import stats
from scipy.stats import spearmanr, kendalltau
from typing import Tuple, Dict, List, Callable, Optional

def calculate_rbo(list1: List, list2: List, p: float = 0.9) -> float:
    """
    Calculate Rank-Biased Overlap (RBO) between two ranked lists.
    
    Formula: RBO = (1 - p) * sum(p^(d-1) * A_d) for d=1 to infinity
    where A_d is the agreement at depth d
    
    Args:
        list1: First ranked list (list of items, ordered by rank)
        list2: Second ranked list (list of items, ordered by rank)
        p: Weight decay parameter (default: 0.9)
        
    Returns:
        RBO score in range [0, 1]
    """
    if not (0 < p < 1):
        raise ValueError(f"Parameter p must be in range (0, 1), got {p}")
    
    if len(list1) == 0 and len(list2) == 0:
        return 1.0
    if len(list1) == 0 or len(list2) == 0:
        return 0.0
    
    # Convert to sets for faster lookup, but preserve order
    set1 = set(list1)
    set2 = set(list2)
    
    # Calculate RBO
    rbo_sum = 0.0
    seen1 = set()
    seen2 = set()
    
    max_depth = max(len(list1), len(list2))
    
    for d in range(1, max_depth + 1):
        # Add items at depth d
        if d <= len(list1):
            seen1.add(list1[d - 1])
        if d <= len(list2):
            seen2.add(list2[d - 1])
        
        # Calculate agreement at depth d
        intersection = seen1 & seen2
        union = seen1 | seen2
        
        if len(union) == 0:
            agreement = 0.0
        else:
            agreement = len(intersection) / len(union)
        
        # Weight by p^(d-1)
        rbo_sum += (p ** (d - 1)) * agreement
    
    # Normalize by (1 - p)
    rbo = (1 - p) * rbo_sum
    
    return rbo


def bootstrap_ci(
    data_x: np.ndarray,
    data_y: np.ndarray,
    func: Callable,
    n_boot: int = 2000
) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval using bootstrap resampling.
    
    Args:
        data_x: First array of paired data
        data_y: Second array of paired data
        func: Function that takes (x, y) arrays and returns a scalar statistic
        n_boot: Number of bootstrap iterations (default: 2000)
        
    Returns:
        Tuple of (lower_bound, upper_bound) for 95% confidence interval
    """
    if len(data_x) != len(data_y):
        raise ValueError(f"data_x and data_y must have same length, got {len(data_x)} and {len(data_y)}")
    
    n = len(data_x)
    bootstrap_stats = []
    
    np.random.seed(42)  # For reproducibility
    
    for _ in range(n_boot):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = data_x[indices]
        y_boot = data_y[indices]
        
        # Calculate statistic on bootstrap sample
        try:
            stat = func(x_boot, y_boot)
            if np.isfinite(stat):
                bootstrap_stats.append(stat)
        except Exception:
            # Skip invalid bootstrap samples
            continue
    
    if len(bootstrap_stats) == 0:
        return (np.nan, np.nan)
    
    # Calculate 95% CI (2.5th and 97.5th percentiles)
    lower = np.percentile(bootstrap_stats, 2.5)
    upper = np.percentile(bootstrap_stats, 97.5)
    
    return (lower, upper)


def calculate_spearman_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation coefficient and p-value.
    Uses permutation test for N < 30.
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length, got {len(x)} and {len(y)}")
    
    # Remove NaN pairs
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    n = len(x_clean)
    
    if n < 2:
        return (np.nan, np.nan)
    
    # Calculate correlation coefficient
    rho, _ = spearmanr(x_clean, y_clean)
    
    # Calculate p-value based on sample size
    if n < 30:
        def statistic(x_data, y_data):
            return spearmanr(x_data, y_data)[0]
        
        try:
            result = stats.permutation_test(
                (x_clean, y_clean),
                statistic,
                permutation_type='pairings',
                n_resamples=2000,
                random_state=42,
                alternative='two-sided'
            )
            p_value = result.pvalue
        except AttributeError:
            # Fallback for older scipy versions
            _, p_value = spearmanr(x_clean, y_clean)
        
    else:
        _, p_value = spearmanr(x_clean, y_clean)
    
    return (rho, p_value)


def calculate_kendall_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Kendall's tau correlation coefficient and p-value.
    Uses permutation test for N < 30.
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length, got {len(x)} and {len(y)}")
    
    # Remove NaN pairs
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    n = len(x_clean)
    
    if n < 2:
        return (np.nan, np.nan)
    
    # Calculate correlation coefficient
    tau, _ = kendalltau(x_clean, y_clean)
    
    # Calculate p-value based on sample size
    if n < 30:
        def statistic(x_data, y_data):
            return kendalltau(x_data, y_data)[0]
        
        try:
            result = stats.permutation_test(
                (x_clean, y_clean),
                statistic,
                permutation_type='pairings',
                n_resamples=2000,
                random_state=42,
                alternative='two-sided'
            )
            p_value = result.pvalue
        except AttributeError:
            # Fallback for older scipy versions
            _, p_value = kendalltau(x_clean, y_clean)
        
    else:
        _, p_value = kendalltau(x_clean, y_clean)
    
    return (tau, p_value)
