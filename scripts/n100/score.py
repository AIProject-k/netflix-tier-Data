"""N100 score v1. Every component returns 0..100; `combine` applies WEIGHTS.

See docs/n100-score-v1.md for the rationale. All constants live in config.py.
"""

from __future__ import annotations

from .config import (
    DECAY_FLOOR,
    DECAY_WEEKLY,
    GLOBAL_SPREAD_MAX,
    GLOBAL_TOP10_BONUS,
    LONGEVITY_BONUS,
    LONGEVITY_MAX,
    MOMENTUM_LOOKBACK,
    RANK_POINTS,
    WEIGHTS,
)


def decay(weeks_ago: int) -> float:
    if 0 <= weeks_ago < len(DECAY_WEEKLY):
        return DECAY_WEEKLY[weeks_ago]
    return DECAY_FLOOR


def rank_points(rank: int) -> int:
    return RANK_POINTS.get(rank, 0)


def rank_score(appearances: list[tuple[int, int]]) -> float:
    """Mean rank-points across every weekly appearance in the window."""
    if not appearances:
        return 0.0
    return sum(rank_points(rank) for _, rank in appearances) / len(appearances)


def recency_score(appearances: list[tuple[int, int]]) -> float:
    """Decay multiplier of the most recent appearance, as 0..100."""
    if not appearances:
        return 0.0
    weeks_ago = min(wa for wa, _ in appearances)
    return decay(weeks_ago) * 100.0


def longevity_score(peak_cum_weeks: int) -> float:
    bonus = 0
    for threshold in sorted(LONGEVITY_BONUS):
        if peak_cum_weeks >= threshold:
            bonus = LONGEVITY_BONUS[threshold]
    return min(100.0, bonus / LONGEVITY_MAX * 100.0)


def momentum_score(points_by_weeks_ago: dict[int, int]) -> float:
    """This week's rank points vs the average of the previous weeks. 50 = flat."""
    this_week = points_by_weeks_ago.get(0, 0)
    prior = [points_by_weeks_ago.get(w, 0) for w in range(1, MOMENTUM_LOOKBACK + 1)]
    avg_prior = sum(prior) / MOMENTUM_LOOKBACK
    delta = this_week - avg_prior
    return max(0.0, min(100.0, 50.0 + delta / 2.0))


def global_score(countries_charting: int, tracked_count: int, in_global_top10: bool) -> float:
    spread = (countries_charting / tracked_count) * GLOBAL_SPREAD_MAX if tracked_count else 0.0
    return min(100.0, spread + (GLOBAL_TOP10_BONUS if in_global_top10 else 0.0))


def combine(components: dict[str, float]) -> float:
    return sum(WEIGHTS[name] * components[name] for name in WEIGHTS)
