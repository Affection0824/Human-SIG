"""Compatibility build of the :mod:`rbo` package used by Human-SIG."""

from .rbo import RankingSimilarity, rbo, rbo_ext, top_weightness

__all__ = ["RankingSimilarity", "rbo", "rbo_ext", "top_weightness"]
