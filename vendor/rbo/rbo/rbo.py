"""Local compatibility implementation of the upstream ``rbo`` package.

This module is vendored so the project can keep ``import rbo`` available
without inheriting the upstream dependency constraint that pins NumPy to
``<2.0`` on Python 3.14.
"""

from __future__ import annotations

from typing import List, Optional, Union

import numpy as np
from tqdm import tqdm


class RankingSimilarity:
    """Compute similarity between two ranked lists."""

    def __init__(
        self,
        S: Union[List, np.ndarray],
        T: Union[List, np.ndarray],
        verbose: bool = False,
    ) -> None:
        assert type(S) in [list, np.ndarray]
        assert type(T) in [list, np.ndarray]
        assert len(S) == len(set(S))
        assert len(T) == len(set(T))
        self.S, self.T = S, T
        self.N_S, self.N_T = len(S), len(T)
        self.verbose = verbose
        self.p = 0.5

    def assert_p(self, p: float) -> None:
        """Validate and store the persistence parameter."""
        assert 0.0 < p < 1.0, "p must be between (0, 1)"
        self.p = p

    def _bound_range(self, value: float) -> float:
        """Clamp a numeric value to the ``[0, 1]`` interval."""
        try:
            assert 0 <= value <= 1 or np.isclose(1, value)
            return value
        except AssertionError:
            larger_than_zero = max(0.0, value)
            return min(1.0, larger_than_zero)

    def rbo(
        self,
        k: Optional[float] = None,
        p: float = 1.0,
        ext: bool = False,
    ) -> float:
        """Compute weighted rank-biased overlap.

        This matches the public API of the upstream package closely enough for
        ad-hoc use in this repository.
        """
        if not self.N_S and not self.N_T:
            return 1.0
        if not self.N_S or not self.N_T:
            return 0.0
        if k is None:
            k = float("inf")
        k = int(min(self.N_S, self.N_T, k))

        A, AO = [0.0] * k, [0.0] * k
        if p == 1.0:
            weights = [1.0 for _ in range(k)]
        else:
            self.assert_p(p)
            weights = [(1.0 - p) * p**d for d in range(k)]

        S_running, T_running = {self.S[0]: True}, {self.T[0]: True}
        A[0] = 1.0 if self.S[0] == self.T[0] else 0.0
        AO[0] = weights[0] if self.S[0] == self.T[0] else 0.0
        for d in tqdm(range(1, k), disable=not self.verbose):
            overlap_incr = 0
            if self.S[d] in T_running:
                overlap_incr += 1
            if self.T[d] in S_running:
                overlap_incr += 1
            if self.S[d] == self.T[d]:
                overlap_incr += 1
            A[d] = ((A[d - 1] * d) + overlap_incr) / (d + 1)
            if p == 1.0:
                AO[d] = ((AO[d - 1] * d) + A[d]) / (d + 1)
            else:
                AO[d] = AO[d - 1] + weights[d] * A[d]
            S_running[self.S[d]] = True
            T_running[self.T[d]] = True
        if ext and p < 1:
            return self._bound_range(AO[-1] + A[-1] * p**k)
        return self._bound_range(AO[-1])

    def rbo_ext(self, p: float = 0.98) -> float:
        """Compute the extrapolated rank-biased overlap."""
        self.assert_p(p)
        if not self.N_S and not self.N_T:
            return 1.0
        if not self.N_S or not self.N_T:
            return 0.0

        if len(self.S) > len(self.T):
            L, S = self.S, self.T
        else:
            S, L = self.S, self.T
        s, l = len(S), len(L)

        X, A, rbo_vals = [0.0] * l, [0.0] * l, [0.0] * l
        S_running, L_running = {S[0]}, {L[0]}
        X[0] = 1.0 if S[0] == L[0] else 0.0
        A[0] = X[0]
        rbo_vals[0] = (1.0 - p) * A[0]
        disjoint = 0.0
        ext_term = A[0] * p
        for d in tqdm(range(1, l), disable=not self.verbose):
            if d < s:
                S_running.add(S[d])
                L_running.add(L[d])
                overlap_incr = 0
                if S[d] == L[d]:
                    overlap_incr += 1
                else:
                    if S[d] in L_running:
                        overlap_incr += 1
                    if L[d] in S_running:
                        overlap_incr += 1
                X[d] = X[d - 1] + overlap_incr
                A[d] = 2.0 * X[d] / (len(S_running) + len(L_running))
                rbo_vals[d] = rbo_vals[d - 1] + (1.0 - p) * (p**d) * A[d]
                ext_term = A[d] * p ** (d + 1)
            else:
                L_running.add(L[d])
                overlap_incr = 1.0 if L[d] in S_running else 0.0
                X[d] = X[d - 1] + overlap_incr
                A[d] = X[d] / (d + 1)
                rbo_vals[d] = rbo_vals[d - 1] + (1.0 - p) * (p**d) * A[d]
                X_s = X[s - 1]
                disjoint += (1.0 - p) * (p**d) * (X_s * (d + 1 - s) / (d + 1) / s)
                ext_term = ((X[d] - X_s) / (d + 1) + X[s - 1] / s) * p ** (d + 1)
        return self._bound_range(rbo_vals[-1] + disjoint + ext_term)

    def top_weightness(
        self,
        p: Optional[float] = None,
        d: Optional[int] = None,
    ) -> float:
        """Estimate how much weight is concentrated near the top of the list."""
        self.assert_p(p)
        if d is None:
            d = min(self.N_S, self.N_T)
        else:
            d = min(self.N_S, self.N_T, int(d))
        if d == 0:
            top_w = 1.0
        elif d == 1:
            top_w = 1 - 1 + (1.0 - p) / p * np.log(1.0 / (1 - p))
        else:
            sum_1 = 0.0
            for i in range(1, d):
                sum_1 += p**i / i
            top_w = 1 - p**i + (1.0 - p) / p * (i + 1) * (np.log(1.0 / (1 - p)) - sum_1)
        if self.verbose:
            print(
                "The first {} ranks have {:6.3%} of the weight of the evaluation.".format(
                    d, top_w
                )
            )
        return self._bound_range(top_w)


def rbo(S: Union[List, np.ndarray], T: Union[List, np.ndarray], p: float = 0.9) -> float:
    """Convenience wrapper that mirrors the upstream package's common usage."""
    return RankingSimilarity(S, T).rbo(p=p)


def rbo_ext(S: Union[List, np.ndarray], T: Union[List, np.ndarray], p: float = 0.98) -> float:
    """Convenience wrapper for extrapolated RBO."""
    return RankingSimilarity(S, T).rbo_ext(p=p)


def top_weightness(
    S: Union[List, np.ndarray],
    T: Union[List, np.ndarray],
    p: float,
    d: Optional[int] = None,
) -> float:
    """Convenience wrapper for top-weightness."""
    return RankingSimilarity(S, T).top_weightness(p=p, d=d)
