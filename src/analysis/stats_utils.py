"""
Advanced Statistical Utility Functions for Small-N Analysis

Purpose:
    This module provides rigorous statistical functions specifically designed for small sample
    size analysis (N=28 benchmarks). The methods implemented here are appropriate for small-N
    datasets where standard asymptotic approximations may not hold.

Mathematical Foundations:
    - Rank-Biased Overlap (RBO): Measures ranking similarity with emphasis on top-ranked items
    - Bootstrap Resampling: Non-parametric method for confidence interval estimation without
      distributional assumptions
    - Holm-Bonferroni Correction: Sequential multiple comparison correction that is less
      conservative than standard Bonferroni
    - Huber Loss Regression: Robust regression that minimizes impact of outliers in small-N
      datasets
    - Monte Carlo Permutation Tests: p-value estimation for small samples (N < 30)

Why These Methods for Small-N:
    - Monte Carlo permutation tests avoid asymptotic distributional approximations
    - Bootstrap resampling allows confidence interval estimation without distributional assumptions
    - Robust regression (Huber loss) reduces sensitivity to outliers, which is critical when
      sample size is small
    - RBO focuses on top-ranked items, which is more relevant for benchmark evaluation

Input/Output:
    - Functions accept numpy arrays or pandas Series
    - Return values include correlation coefficients, p-values, confidence intervals, and
      corrected significance levels
"""

import numpy as np
from scipy import stats
from scipy.stats import spearmanr, kendalltau
from typing import Tuple, Dict, List, Callable, Optional
from statsmodels.robust.norms import HuberT
from statsmodels.robust.robust_linear_model import RLM


def calculate_rbo(list1: List, list2: List, p: float = 0.9) -> float:
    """
    Calculate extrapolated Rank-Biased Overlap for finite ranked lists.

    Agreement at depth d is the common-prefix overlap divided by d. Both inputs
    must contain the same number of items because this workflow first projects
    both rankings onto the same common-model universe. For length k, the finite
    extrapolated score is the observed weighted sum through k plus
    ``A_k * p**k``.

    Args:
        list1: First ranked list (list of items, ordered by rank)
        list2: Second ranked list (list of items, ordered by rank)
        p: Persistence parameter in (0, 1); smaller values put more weight on
           the top of the rankings.

    Returns:
        RBO_EXT score in [0, 1].

    Raises:
        ValueError: If p is invalid, lengths differ, or either list contains
            duplicate items.
    """
    if not (0 < p < 1):
        raise ValueError(f"Parameter p must be in range (0, 1), got {p}")

    if len(list1) != len(set(list1)) or len(list2) != len(set(list2)):
        raise ValueError("RBO input rankings must not contain duplicate items")

    if len(list1) != len(list2):
        raise ValueError(
            "RBO input rankings must have equal length after common-model projection"
        )

    if len(list1) == 0:
        return 1.0

    seen_1 = set()
    seen_2 = set()
    weighted_sum = 0.0
    agreement = 0.0

    for depth, (item_1, item_2) in enumerate(zip(list1, list2), start=1):
        seen_1.add(item_1)
        seen_2.add(item_2)
        agreement = len(seen_1 & seen_2) / depth
        weighted_sum += (1.0 - p) * p ** (depth - 1) * agreement

    result = weighted_sum + agreement * p ** len(list1)
    return float(min(1.0, max(0.0, result)))


def bootstrap_ci(
    data_x: np.ndarray,
    data_y: np.ndarray,
    func: Callable,
    n_boot: int = 2000
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
        n_boot: Number of bootstrap iterations (default: 2000)
        
    Returns:
        Tuple of (lower_bound, upper_bound) for 95% confidence interval
        
    Raises:
        ValueError: If data_x and data_y have different lengths
    """
    lower, upper = bootstrap_vector_ci(
        data_x,
        data_y,
        func,
        n_boot=n_boot,
        n_statistics=1,
    )
    return (float(lower[0]), float(upper[0]))


def bootstrap_vector_ci(
    data_x: np.ndarray,
    data_y: np.ndarray,
    func: Callable,
    n_boot: int = 2000,
    n_statistics: int = 1,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate percentile bootstrap CIs for one or more statistics.

    ``func`` is evaluated once per resample and may return either a scalar or
    a one-dimensional array. Vector output is useful when several statistics,
    such as multiple regression coefficients, come from the same fitted model:
    every statistic then uses exactly the same bootstrap samples without
    fitting the model more than once per iteration.

    Invalid values are omitted independently for each statistic. Exceptions
    raised by ``func`` mark the whole resample as invalid. A local legacy NumPy
    random generator preserves the sampling sequence previously produced by
    ``np.random.seed(42)`` without modifying global random state.

    Args:
        data_x: First array of paired observations. It may be one- or
            multi-dimensional, with observations along the first axis.
        data_y: Second array of paired observations.
        func: Function returning a scalar or one-dimensional statistic array.
        n_boot: Number of bootstrap iterations.
        n_statistics: Expected number of returned statistics.
        progress_callback: Optional callback receiving ``(completed, total)``
            once per iteration.

    Returns:
        Two arrays containing the lower and upper 95% confidence bounds.

    Raises:
        ValueError: If input lengths, iteration count, or statistic shape is
            invalid.
    """
    data_x = np.asarray(data_x)
    data_y = np.asarray(data_y)

    if len(data_x) != len(data_y):
        raise ValueError(
            "data_x and data_y must have same length, "
            f"got {len(data_x)} and {len(data_y)}"
        )
    if n_boot <= 0:
        raise ValueError(f"n_boot must be positive, got {n_boot}")
    if n_statistics <= 0:
        raise ValueError(
            f"n_statistics must be positive, got {n_statistics}"
        )

    n = len(data_x)
    if n == 0:
        empty_bounds = np.full(n_statistics, np.nan, dtype=float)
        return empty_bounds.copy(), empty_bounds.copy()

    rng = np.random.RandomState(42)
    bootstrap_stats = np.full((n_boot, n_statistics), np.nan, dtype=float)

    for iteration in range(n_boot):
        if progress_callback is not None:
            progress_callback(iteration + 1, n_boot)

        indices = rng.choice(n, size=n, replace=True)
        try:
            statistic = np.asarray(
                func(data_x[indices], data_y[indices]),
                dtype=float,
            )
        except Exception:
            continue

        statistic = np.atleast_1d(statistic)
        if statistic.ndim != 1 or statistic.size != n_statistics:
            raise ValueError(
                "func must return a scalar or one-dimensional array with "
                f"{n_statistics} value(s); got shape {statistic.shape}"
            )

        finite = np.isfinite(statistic)
        bootstrap_stats[iteration, finite] = statistic[finite]

    lower = np.full(n_statistics, np.nan, dtype=float)
    upper = np.full(n_statistics, np.nan, dtype=float)
    for statistic_index in range(n_statistics):
        valid_values = bootstrap_stats[:, statistic_index]
        valid_values = valid_values[np.isfinite(valid_values)]
        if valid_values.size > 0:
            lower[statistic_index], upper[statistic_index] = np.percentile(
                valid_values,
                [2.5, 97.5],
            )

    return lower, upper


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
    5. Make adjusted p-values monotone by taking the cumulative maximum of
       (m - i + 1) * p(i), capped at 1
    
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
    cumulative_adjusted_p = 0.0
    
    for rank, (hypothesis, p_raw) in enumerate(sorted_items, start=1):
        # Adjusted significance level: alpha / (m - rank + 1)
        adjusted_alpha = alpha / (m - rank + 1)
        
        # Holm adjusted p-values are cumulative maxima of the scaled p-values.
        # Without this step, adjusted values can decrease as raw p-values grow.
        scaled_p = p_raw * (m - rank + 1)
        cumulative_adjusted_p = max(cumulative_adjusted_p, scaled_p)
        p_corrected = min(cumulative_adjusted_p, 1.0)
        
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
            - 'fittedvalues': predicted values
            - Additional model statistics
    """
    model = RLM(y, X, M=HuberT())
    results = model.fit()

    coefficients = results.params
    results_dict = {
        'coefficients': coefficients,
        'pvalues': results.pvalues,
        'fittedvalues': results.fittedvalues,
        'resid': results.resid,
        'df_resid': results.df_resid,
        'df_model': results.df_model,
    }

    return coefficients, results_dict


def calculate_spearman_with_pvalue(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation coefficient and p-value.
    
    For small sample sizes (N < 30), estimates the p-value with a fixed-seed
    Monte Carlo permutation test using 2,000 random permutations.
    For larger samples (N >= 30), uses asymptotic approximation from scipy.stats.spearmanr.
    
    Rationale for conditional logic:
    - Monte Carlo permutation tests avoid asymptotic distributional assumptions
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
        # Use a fixed-seed Monte Carlo permutation test for small samples.
        def statistic(x_data, y_data):
            # Permute y_data under null hypothesis
            return spearmanr(x_data, y_data)[0]
        
        # Permutation test with pairings (preserves pairing structure)
        # Use 2,000 random permutations for a stable, reproducible estimate.
        result = stats.permutation_test(
            (x_clean, y_clean),
            statistic,
            permutation_type='pairings',
            n_resamples=2000,
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
    
    For small sample sizes (N < 30), estimates the p-value with a fixed-seed
    Monte Carlo permutation test using 2,000 random permutations.
    For larger samples (N >= 30), uses asymptotic approximation from scipy.stats.kendalltau.
    
    Rationale for conditional logic:
    - Monte Carlo permutation tests avoid asymptotic distributional assumptions
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
        # Use a fixed-seed Monte Carlo permutation test for small samples.
        def statistic(x_data, y_data):
            # Permute y_data under null hypothesis
            return kendalltau(x_data, y_data)[0]
        
        # Permutation test with pairings (preserves pairing structure)
        # Use 2,000 random permutations for a stable, reproducible estimate.
        result = stats.permutation_test(
            (x_clean, y_clean),
            statistic,
            permutation_type='pairings',
            n_resamples=2000,
            random_state=42,
            alternative='two-sided'
        )
        
        p_value = result.pvalue
        
    else:
        # Use asymptotic approximation for larger samples
        _, p_value = kendalltau(x_clean, y_clean)
    
    return (tau, p_value)

