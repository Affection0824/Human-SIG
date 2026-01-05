"""
Advanced Statistical Utility Functions for Small-N Analysis

Purpose:
    This module provides rigorous statistical functions specifically designed for small sample
    size analysis (N=29 benchmarks). The methods implemented here are appropriate for small-N
    datasets where standard asymptotic approximations may not hold.

Mathematical Foundations:
    - Fisher Z-Transform: Converts correlation coefficients to approximately normal distribution
      for averaging and aggregation
    - Rank-Biased Overlap (RBO): Measures ranking similarity with emphasis on top-ranked items
    - Bootstrap Resampling: Non-parametric method for confidence interval estimation without
      distributional assumptions
    - Holm-Bonferroni Correction: Sequential multiple comparison correction that is less
      conservative than standard Bonferroni
    - Huber Loss Regression: Robust regression that minimizes impact of outliers in small-N
      datasets
    - Permutation Tests: Exact p-value calculation for small sample sizes (N < 30)

Why These Methods for Small-N:
    - Permutation tests provide exact p-values without relying on asymptotic approximations
    - Bootstrap resampling allows confidence interval estimation without distributional assumptions
    - Robust regression (Huber loss) reduces sensitivity to outliers, which is critical when
      sample size is small
    - RBO focuses on top-ranked items, which is more relevant for benchmark evaluation
    - Fisher Z-transform enables proper aggregation of correlation coefficients

Input/Output:
    - Functions accept numpy arrays or pandas Series
    - Return values include correlation coefficients, p-values, confidence intervals, and
      corrected significance levels
"""

import numpy as np
from scipy import stats
from scipy.stats import spearmanr, kendalltau
from typing import Tuple, Dict, List, Callable, Optional
import warnings


def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher Z-transformation to correlation coefficient.
    
    Formula: z = arctanh(r) = 0.5 * ln((1 + r) / (1 - r))
    
    The Fisher transformation converts correlation coefficients to an approximately
    normal distribution, which is useful for:
    - Averaging multiple correlation coefficients
    - Computing confidence intervals for correlations
    - Statistical tests on correlation coefficients
    
    Args:
        r: Correlation coefficient (must be in range [-1, 1])
        
    Returns:
        Fisher Z-transformed value
        
    Raises:
        ValueError: If r is not in valid range [-1, 1]
    """
    if not (-1 <= r <= 1):
        raise ValueError(f"Correlation coefficient must be in range [-1, 1], got {r}")
    
    # Handle edge cases
    if abs(r) >= 1.0:
        # Return large finite value instead of inf
        return np.sign(r) * 10.0
    
    return np.arctanh(r)


def calculate_rbo(list1: List, list2: List, p: float = 0.9) -> float:
    """
    Calculate Rank-Biased Overlap (RBO) between two ranked lists.
    
    RBO measures ranking similarity with emphasis on top-ranked items.
    The parameter p (0 < p < 1) controls the weight decay: smaller p gives more
    weight to top-ranked items. p=0.9 is a standard choice that focuses on top 10 items.
    
    Formula: RBO = (1 - p) * sum(p^(d-1) * A_d) for d=1 to infinity
    where A_d is the agreement at depth d (proportion of items in both lists up to depth d)
    
    Args:
        list1: First ranked list (list of items, ordered by rank)
        list2: Second ranked list (list of items, ordered by rank)
        p: Weight decay parameter (default: 0.9). Must be in (0, 1).
           Smaller p = more weight on top items. p=0.9 focuses on top ~10 items.
        
    Returns:
        RBO score in range [0, 1], where 1 indicates identical rankings
        and 0 indicates no overlap
        
    Raises:
        ValueError: If p is not in valid range (0, 1)
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
    n_boot: int = 5000
) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval using bootstrap resampling.
    
    Bootstrap methodology:
    1. Resample n_boot times with replacement from the paired data (data_x, data_y)
    2. Apply func to each bootstrap sample to get a statistic
    3. Use 2.5th and 97.5th percentiles of bootstrap distribution as CI bounds
    
    This method makes no distributional assumptions and is appropriate for
    small sample sizes where asymptotic approximations may not hold.
    
    Args:
        data_x: First array of paired data
        data_y: Second array of paired data (must have same length as data_x)
        func: Function that takes (x, y) arrays and returns a scalar statistic
              (e.g., correlation coefficient)
        n_boot: Number of bootstrap iterations (default: 5000)
        
    Returns:
        Tuple of (lower_bound, upper_bound) for 95% confidence interval
        
    Raises:
        ValueError: If data_x and data_y have different lengths
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


def holm_bonferroni_correction(p_values_dict: Dict[str, float], alpha: float = 0.05) -> Dict[str, Dict]:
    """
    Apply Holm-Bonferroni correction for multiple comparisons.
    
    The Holm-Bonferroni method is a sequential correction procedure that is less
    conservative than the standard Bonferroni correction while still controlling
    the family-wise error rate (FWER).
    
    Algorithm:
    1. Sort p-values from smallest to largest: p(1) <= p(2) <= ... <= p(m)
    2. For each p-value p(i), compare to alpha / (m - i + 1)
    3. Reject null hypothesis for p(i) if p(i) <= alpha / (m - i + 1)
    4. Once a hypothesis is not rejected, all subsequent hypotheses are also not rejected
    
    Args:
        p_values_dict: Dictionary mapping hypothesis names to raw p-values
                      Format: {hypothesis_name: raw_p_value}
        alpha: Significance level (default: 0.05)
        
    Returns:
        Dictionary mapping hypothesis names to correction results:
        {
            hypothesis_name: {
                'p_raw': raw p-value,
                'p_corrected': adjusted p-value (or None if not applicable),
                'is_significant': boolean indicating significance after correction
            }
        }
    """
    if len(p_values_dict) == 0:
        return {}
    
    # Sort p-values from smallest to largest
    sorted_items = sorted(p_values_dict.items(), key=lambda x: x[1])
    m = len(sorted_items)
    
    results = {}
    found_non_significant = False
    
    for rank, (hypothesis, p_raw) in enumerate(sorted_items, start=1):
        # Adjusted significance level: alpha / (m - rank + 1)
        adjusted_alpha = alpha / (m - rank + 1)
        
        # Calculate adjusted p-value (multiply by (m - rank + 1), cap at 1.0)
        p_corrected = min(p_raw * (m - rank + 1), 1.0)
        
        # Check significance
        if found_non_significant:
            # Once we find a non-significant result, all subsequent are also non-significant
            is_significant = False
        else:
            is_significant = p_raw <= adjusted_alpha
        
        if not is_significant:
            found_non_significant = True
        
        results[hypothesis] = {
            'p_raw': p_raw,
            'p_corrected': p_corrected,
            'is_significant': is_significant
        }
    
    return results


def huber_loss_regression(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Perform robust regression using Huber loss function.
    
    Huber loss is less sensitive to outliers than ordinary least squares (OLS),
    making it appropriate for small-N datasets where outliers can have
    disproportionate influence.
    
    Huber loss function:
    - For small residuals (|r| <= epsilon): quadratic loss (like OLS)
    - For large residuals (|r| > epsilon): linear loss (reduces outlier influence)
    
    This implementation uses statsmodels.RLM (Robust Linear Model) with Huber's
    t-criterion, which is specifically designed for robust estimation.
    
    Args:
        X: Design matrix (n_samples, n_features). Should include intercept column if needed.
        y: Target vector (n_samples,)
        
    Returns:
        Tuple of (coefficients, results_dict):
        - coefficients: Array of regression coefficients (including intercept if included)
        - results_dict: Dictionary containing:
            - 'pvalues': p-values for each coefficient
            - 'rsquared': R-squared value
            - 'fittedvalues': predicted values
            - Additional model statistics
    """
    try:
        from statsmodels.robust.robust_linear_model import RLM
        from statsmodels.robust.norms import HuberT
        
        # Create RLM model with Huber's t-criterion
        model = RLM(y, X, M=HuberT())
        results = model.fit()
        
        coefficients = results.params
        pvalues = results.pvalues
        
        results_dict = {
            'coefficients': coefficients,
            'pvalues': pvalues,
            'rsquared': results.rsquared if hasattr(results, 'rsquared') else np.nan,
            'fittedvalues': results.fittedvalues,
            'resid': results.resid,
            'df_resid': results.df_resid,
            'df_model': results.df_model
        }
        
        return coefficients, results_dict
        
    except ImportError:
        # Fallback to sklearn if statsmodels not available
        try:
            from sklearn.linear_model import HuberRegressor
            
            model = HuberRegressor(epsilon=1.35, max_iter=200, alpha=0.0)
            model.fit(X, y)
            
            coefficients = np.append(model.intercept_, model.coef_)
            
            # Approximate p-values using t-test (not exact for Huber regression)
            y_pred = model.predict(X)
            residuals = y - y_pred
            mse = np.mean(residuals ** 2)
            
            # Simple approximation (not exact for robust regression)
            results_dict = {
                'coefficients': coefficients,
                'pvalues': np.full(len(coefficients), np.nan),  # Not available in sklearn
                'rsquared': model.score(X, y),
                'fittedvalues': y_pred,
                'resid': residuals
            }
            
            return coefficients, results_dict
            
        except ImportError:
            raise ImportError(
                "Neither statsmodels nor sklearn available. "
                "Please install statsmodels (recommended) or sklearn for robust regression."
            )


def calculate_spearman_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation coefficient and p-value.
    
    For small sample sizes (N < 30), uses permutation test for exact p-value calculation.
    For larger samples (N >= 30), uses asymptotic approximation from scipy.stats.spearmanr.
    
    Rationale for conditional logic:
    - Permutation tests provide exact p-values without distributional assumptions
    - For small N, asymptotic approximations may be inaccurate
    - For large N, asymptotic approximation is sufficiently accurate and computationally efficient
    
    Args:
        x: First array of paired data
        y: Second array of paired data (must have same length as x)
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
        
    Raises:
        ValueError: If x and y have different lengths or insufficient data
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
        # Use permutation test for small sample sizes
        def statistic(x_data, y_data):
            # Permute y_data under null hypothesis
            return spearmanr(x_data, y_data)[0]
        
        # Permutation test with pairings (preserves pairing structure)
        result = stats.permutation_test(
            (x_clean, y_clean),
            statistic,
            permutation_type='pairings',
            n_resamples=10000,
            random_state=42,
            alternative='two-sided'
        )
        
        p_value = result.pvalue
        
    else:
        # Use asymptotic approximation for larger samples
        _, p_value = spearmanr(x_clean, y_clean)
    
    return (rho, p_value)


def calculate_kendall_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Kendall's tau correlation coefficient and p-value.
    
    For small sample sizes (N < 30), uses permutation test for exact p-value calculation.
    For larger samples (N >= 30), uses asymptotic approximation from scipy.stats.kendalltau.
    
    Rationale for conditional logic:
    - Permutation tests provide exact p-values without distributional assumptions
    - For small N, asymptotic approximations may be inaccurate
    - For large N, asymptotic approximation is sufficiently accurate and computationally efficient
    
    Args:
        x: First array of paired data
        y: Second array of paired data (must have same length as x)
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
        
    Raises:
        ValueError: If x and y have different lengths or insufficient data
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
        # Use permutation test for small sample sizes
        def statistic(x_data, y_data):
            # Permute y_data under null hypothesis
            return kendalltau(x_data, y_data)[0]
        
        # Permutation test with pairings (preserves pairing structure)
        result = stats.permutation_test(
            (x_clean, y_clean),
            statistic,
            permutation_type='pairings',
            n_resamples=10000,
            random_state=42,
            alternative='two-sided'
        )
        
        p_value = result.pvalue
        
    else:
        # Use asymptotic approximation for larger samples
        _, p_value = kendalltau(x_clean, y_clean)
    
    return (tau, p_value)

