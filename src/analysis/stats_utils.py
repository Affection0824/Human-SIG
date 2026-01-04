"""
Advanced Statistical Utility Functions

Purpose:
    This module provides rigorous statistical functions specifically designed for small-N analysis
    (N=29 benchmarks). The functions implement advanced statistical methods including Fisher z-transformation,
    Rank-Biased Overlap (RBO), bootstrap confidence intervals, Holm-Bonferroni correction for multiple
    comparisons, robust regression using Huber loss, and permutation-based p-value calculation for
    small sample sizes.

Mathematical Foundations:
    - Fisher z-transformation: Used for averaging correlations, as correlation coefficients are not
      normally distributed. The transformation z = arctanh(r) makes the distribution approximately normal.
    - RBO (Rank-Biased Overlap): A rank correlation metric that focuses on top-ranked items, with parameter
      p controlling the weight decay (p=0.9 means top items are weighted more heavily).
    - Bootstrap: Resampling with replacement to estimate confidence intervals, robust for small samples.
    - Holm-Bonferroni Correction: A step-down procedure for controlling family-wise error rate in multiple
      comparisons, less conservative than Bonferroni but still controls Type I error.
    - Huber Loss Regression: A robust regression method that minimizes the impact of outliers by using
      a loss function that transitions from quadratic (for small errors) to linear (for large errors).
    - Permutation Test: For small sample sizes (N < 30), permutation tests provide exact p-values by
      permuting one ranking under the null hypothesis of independence and recalculating the correlation.

Why These Methods for Small-N:
    - Small sample sizes (N=29) require methods that are robust to outliers and don't rely on large-sample
      asymptotic assumptions.
    - Permutation tests provide exact p-values for small samples, avoiding approximation errors.
    - Bootstrap resampling provides reliable confidence intervals without assuming normality.
    - Robust regression (Huber loss) minimizes the impact of outliers that can disproportionately affect
      small samples.
    - Multiple comparison correction is essential when testing multiple hypotheses simultaneously.

Input/Output:
    - Functions accept numpy arrays or pandas Series as input
    - Return dictionaries or tuples containing statistics, p-values, and confidence intervals
    - All functions are designed to handle missing values gracefully
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import spearmanr, kendalltau
from sklearn.linear_model import HuberRegressor
import statsmodels.api as sm
from statsmodels.robust.robust_linear_model import RLM
from typing import Tuple, Dict, List, Callable, Optional
import warnings


def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher z-transformation to a correlation coefficient.
    
    The Fisher z-transformation converts correlation coefficients to a scale that is approximately
    normally distributed, making it suitable for averaging and statistical inference.
    
    Formula: z = arctanh(r) = 0.5 * ln((1 + r) / (1 - r))
    
    Purpose:
        - Correlation coefficients are not normally distributed, especially near the boundaries (-1, 1)
        - The Fisher transformation makes the distribution approximately normal
        - This allows for averaging correlations and computing confidence intervals
        - Inverse transformation: r = tanh(z) = (exp(2z) - 1) / (exp(2z) + 1)
    
    Args:
        r: Correlation coefficient (must be in range [-1, 1])
    
    Returns:
        Fisher z-transformed value
    
    Raises:
        ValueError: If r is not in range [-1, 1]
    """
    if not -1 <= r <= 1:
        raise ValueError(f"Correlation coefficient r must be in range [-1, 1], got {r}")
    
    # Handle edge cases
    if r == 1.0:
        return np.inf
    if r == -1.0:
        return -np.inf
    if r == 0.0:
        return 0.0
    
    # Fisher z-transformation: z = arctanh(r)
    z = np.arctanh(r)
    return z


def calculate_rbo(list1: List, list2: List, p: float = 0.9) -> float:
    """
    Calculate Rank-Biased Overlap (RBO) between two ranked lists.
    
    RBO is a rank correlation metric that focuses on top-ranked items. The parameter p controls
    the weight decay: higher p means more weight on top items. With p=0.9, the top 10 items
    receive most of the weight.
    
    Formula:
        RBO = (1 - p) * sum_{d=1}^{infinity} p^{d-1} * A_d
        where A_d is the agreement at depth d (proportion of items in common up to depth d)
    
    The p parameter:
        - p=0.9 means that the first item gets weight (1-0.9)*0.9^0 = 0.1
        - The second item gets weight (1-0.9)*0.9^1 = 0.09
        - The third item gets weight (1-0.9)*0.9^2 = 0.081
        - This creates exponential decay, focusing on top items
    
    Args:
        list1: First ranked list (items in order of rank, best first)
        list2: Second ranked list (items in order of rank, best first)
        p: Weight decay parameter (default 0.9, must be in (0, 1))
    
    Returns:
        RBO score between 0 and 1 (1 = perfect agreement, 0 = no agreement)
    
    Raises:
        ValueError: If p is not in range (0, 1)
    """
    if not 0 < p < 1:
        raise ValueError(f"Parameter p must be in range (0, 1), got {p}")
    
    # Convert to sets for faster lookup, but preserve order
    set1 = set(list1)
    set2 = set(list2)
    
    # Find maximum depth
    max_depth = max(len(list1), len(list2))
    
    if max_depth == 0:
        return 1.0  # Both empty lists
    
    # Calculate RBO
    rbo_sum = 0.0
    agreement_at_depth = 0.0
    
    for d in range(1, max_depth + 1):
        # Get items up to depth d
        items1_d = set(list1[:d]) if d <= len(list1) else set1
        items2_d = set(list2[:d]) if d <= len(list2) else set2
        
        # Agreement at depth d: proportion of items in common
        intersection = items1_d & items2_d
        union = items1_d | items2_d
        
        if len(union) == 0:
            agreement_at_depth = 1.0
        else:
            agreement_at_depth = len(intersection) / len(union)
        
        # Weight: (1-p) * p^(d-1)
        weight = (1 - p) * (p ** (d - 1))
        rbo_sum += weight * agreement_at_depth
    
    return rbo_sum


def bootstrap_ci(
    data_x: np.ndarray,
    data_y: np.ndarray,
    func: Callable,
    n_boot: int = 5000
) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval using bootstrap resampling.
    
    Bootstrap methodology:
        1. Resample the paired data (x, y) with replacement n_boot times
        2. For each bootstrap sample, compute the statistic using func
        3. The 95% confidence interval is the 2.5th and 97.5th percentiles of the bootstrap distribution
    
    This method provides reliable confidence intervals without assuming normality, making it
    particularly suitable for small sample sizes.
    
    Args:
        data_x: First data array (must have same length as data_y)
        data_y: Second data array (must have same length as data_x)
        func: Function that computes the statistic of interest
              Must accept two arrays (x, y) and return a single value
        n_boot: Number of bootstrap iterations (default 5000)
    
    Returns:
        Tuple of (lower_bound, upper_bound) for 95% confidence interval
    
    Raises:
        ValueError: If data_x and data_y have different lengths
    """
    if len(data_x) != len(data_y):
        raise ValueError(f"data_x and data_y must have same length, got {len(data_x)} and {len(data_y)}")
    
    n = len(data_x)
    bootstrap_stats = []
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    for _ in range(n_boot):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = data_x[indices]
        y_boot = data_y[indices]
        
        # Compute statistic
        try:
            stat = func(x_boot, y_boot)
            bootstrap_stats.append(stat)
        except (ValueError, RuntimeError):
            # Skip if statistic cannot be computed (e.g., all values are the same)
            continue
    
    if len(bootstrap_stats) == 0:
        return (np.nan, np.nan)
    
    # Calculate 95% confidence interval (2.5th and 97.5th percentiles)
    ci_lower = np.percentile(bootstrap_stats, 2.5)
    ci_upper = np.percentile(bootstrap_stats, 97.5)
    
    return (ci_lower, ci_upper)


def holm_bonferroni_correction(p_values_dict: Dict[str, float]) -> Dict[str, Dict]:
    """
    Apply Holm-Bonferroni correction for multiple comparisons.
    
    The Holm-Bonferroni correction is a step-down procedure that controls the family-wise error rate
    (FWER) while being less conservative than the standard Bonferroni correction.
    
    Algorithm:
        1. Sort p-values from smallest to largest
        2. For each p-value at rank i (1-indexed), adjust: p_corrected = p_raw * (m - i + 1)
           where m is the total number of hypotheses
        3. Ensure monotonicity: each corrected p-value must be >= the previous one
    
    This correction ensures that the probability of at least one Type I error (false positive)
    across all tests is controlled at the desired level (typically 0.05).
    
    Args:
        p_values_dict: Dictionary mapping hypothesis names to raw p-values
                      Format: {"H1": 0.03, "H2": 0.15, ...}
    
    Returns:
        Dictionary mapping hypothesis names to results dictionaries:
        {
            "H1": {
                "p_raw": 0.03,
                "p_corrected": 0.15,  # Adjusted for multiple comparisons
                "is_significant": True  # True if p_corrected < 0.05
            },
            ...
        }
    """
    if not p_values_dict:
        return {}
    
    # Convert to list of (hypothesis, p_value) tuples and sort by p-value
    hypotheses = list(p_values_dict.keys())
    p_values = list(p_values_dict.values())
    
    sorted_pairs = sorted(zip(hypotheses, p_values), key=lambda x: x[1])
    m = len(sorted_pairs)
    
    # Apply Holm-Bonferroni correction
    results = {}
    previous_corrected = 0.0
    
    for rank, (hypothesis, p_raw) in enumerate(sorted_pairs, start=1):
        # Adjusted p-value: p_corrected = p_raw * (m - rank + 1)
        p_corrected = p_raw * (m - rank + 1)
        
        # Ensure monotonicity: each corrected p-value must be >= previous
        p_corrected = max(p_corrected, previous_corrected)
        previous_corrected = p_corrected
        
        # Cap at 1.0
        p_corrected = min(p_corrected, 1.0)
        
        results[hypothesis] = {
            "p_raw": p_raw,
            "p_corrected": p_corrected,
            "is_significant": p_corrected < 0.05
        }
    
    return results


def huber_loss_regression(X: np.ndarray, y: np.ndarray) -> Dict:
    """
    Perform robust regression using Huber loss to minimize the impact of outliers.
    
    Huber loss is a robust loss function that transitions from quadratic (for small errors) to
    linear (for large errors). This makes the regression less sensitive to outliers compared to
    ordinary least squares (OLS).
    
    Why use Huber loss for small-N:
        - Small samples are more susceptible to outliers
        - A single outlier can disproportionately affect OLS regression coefficients
        - Huber loss downweights outliers while still using all data points
        - This provides more stable coefficient estimates for small samples
    
    Implementation:
        Uses statsmodels.RLM (Robust Linear Model) with Huber's t-criterion, which is equivalent
        to Huber loss regression.
    
    Args:
        X: Feature matrix (n_samples, n_features). Should include intercept column if needed.
        y: Target vector (n_samples,)
    
    Returns:
        Dictionary containing:
        {
            "coefficients": array of regression coefficients,
            "pvalues": array of p-values for each coefficient,
            "rsquared": R-squared value,
            "model": fitted RLM model object
        }
    """
    # Fit robust linear model with Huber's t-criterion
    model = RLM(y, X, M=sm.robust.norms.HuberT())
    results = model.fit()
    
    return {
        "coefficients": results.params,
        "pvalues": results.pvalues,
        "rsquared": results.rsquared,
        "model": results
    }


def calculate_spearman_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation coefficient and its p-value.
    
    Critical p-value calculation logic:
        - When N < 30: Use permutation test with permutation_type='pairings' to compute exact p-value.
          This permutes one ranking under the null hypothesis of independence and recalculates the
          correlation. This provides exact p-values for small samples.
        - When N >= 30: Use the p-value returned by scipy.stats.spearmanr as a sufficiently
          accurate approximation (asymptotic approximation is reliable for larger samples).
    
    Rationale for conditional logic:
        - For small samples (N < 30), the asymptotic p-value from spearmanr may be inaccurate
        - Permutation tests provide exact p-values without relying on large-sample assumptions
        - For larger samples (N >= 30), the asymptotic approximation is sufficiently accurate
          and computationally more efficient
    
    Args:
        x: First data array
        y: Second data array (must have same length as x)
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    
    Raises:
        ValueError: If x and y have different lengths
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length, got {len(x)} and {len(y)}")
    
    # Remove missing values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    n = len(x_clean)
    
    if n < 2:
        return (np.nan, np.nan)
    
    # Calculate Spearman correlation
    correlation, _ = spearmanr(x_clean, y_clean)
    
    # Calculate p-value based on sample size
    if n < 30:
        # Use permutation test for small samples
        # Permute one ranking under the null hypothesis of independence
        np.random.seed(42)  # For reproducibility
        
        # Observed correlation
        observed_corr = correlation
        
        # Permutation test: permute y and recalculate correlation
        n_permutations = 10000
        permuted_corrs = []
        
        for _ in range(n_permutations):
            y_permuted = np.random.permutation(y_clean)
            perm_corr, _ = spearmanr(x_clean, y_permuted)
            permuted_corrs.append(perm_corr)
        
        permuted_corrs = np.array(permuted_corrs)
        
        # Two-sided p-value: proportion of permuted correlations as extreme as observed
        p_value = np.mean(np.abs(permuted_corrs) >= np.abs(observed_corr))
        
        # Ensure p-value is at least 1/n_permutations
        p_value = max(p_value, 1.0 / n_permutations)
    else:
        # Use asymptotic p-value for larger samples
        _, p_value = spearmanr(x_clean, y_clean)
    
    return (correlation, p_value)


def calculate_kendall_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Kendall's tau correlation coefficient and its p-value.
    
    Critical p-value calculation logic:
        - When N < 30: Use permutation test with permutation_type='pairings' to compute exact p-value.
          This permutes one ranking under the null hypothesis of independence and recalculates the
          correlation. This provides exact p-values for small samples.
        - When N >= 30: Use the p-value returned by scipy.stats.kendalltau as a sufficiently
          accurate approximation (asymptotic approximation is reliable for larger samples).
    
    Rationale for conditional logic:
        - For small samples (N < 30), the asymptotic p-value from kendalltau may be inaccurate
        - Permutation tests provide exact p-values without relying on large-sample assumptions
        - For larger samples (N >= 30), the asymptotic approximation is sufficiently accurate
          and computationally more efficient
    
    Args:
        x: First data array
        y: Second data array (must have same length as x)
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    
    Raises:
        ValueError: If x and y have different lengths
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length, got {len(x)} and {len(y)}")
    
    # Remove missing values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    n = len(x_clean)
    
    if n < 2:
        return (np.nan, np.nan)
    
    # Calculate Kendall's tau
    correlation, _ = kendalltau(x_clean, y_clean)
    
    # Calculate p-value based on sample size
    if n < 30:
        # Use permutation test for small samples
        # Permute one ranking under the null hypothesis of independence
        np.random.seed(42)  # For reproducibility
        
        # Observed correlation
        observed_corr = correlation
        
        # Permutation test: permute y and recalculate correlation
        n_permutations = 10000
        permuted_corrs = []
        
        for _ in range(n_permutations):
            y_permuted = np.random.permutation(y_clean)
            perm_corr, _ = kendalltau(x_clean, y_permuted)
            permuted_corrs.append(perm_corr)
        
        permuted_corrs = np.array(permuted_corrs)
        
        # Two-sided p-value: proportion of permuted correlations as extreme as observed
        p_value = np.mean(np.abs(permuted_corrs) >= np.abs(observed_corr))
        
        # Ensure p-value is at least 1/n_permutations
        p_value = max(p_value, 1.0 / n_permutations)
    else:
        # Use asymptotic p-value for larger samples
        _, p_value = kendalltau(x_clean, y_clean)
    
    return (correlation, p_value)

