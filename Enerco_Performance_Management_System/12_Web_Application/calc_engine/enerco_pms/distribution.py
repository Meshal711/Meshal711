"""Hybrid bell curve, stage 1: compare actual ratings with the guided distribution.

The guided distribution is a reference, not a quota. This module only reports
variance and flags it for the calibration committee; it never changes a rating.
Variance is judged against a binomial interval, so small groups are not flagged
just because they happen to have no one in a 5% category.
"""

from collections import Counter, defaultdict
from math import comb


def binom_cdf(k, n, p):
    if k < 0:
        return 0.0
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(0, min(k, n) + 1))


def binomial_interval(n, p, confidence):
    """Central interval [lo, hi] of counts expected under the guideline."""
    tail = (1 - confidence) / 2
    lo = 0
    while lo < n and binom_cdf(lo, n, p) < tail:
        lo += 1
    hi = n
    while hi > 0 and 1 - binom_cdf(hi - 1, n, p) < tail:
        hi -= 1
    return lo, hi


def group_status(n, cfg):
    if n >= cfg["dist_min_group_size_full"]:
        return "FULL_COMPARISON"
    if n >= cfg["dist_min_group_size_indicative"]:
        return "INDICATIVE_ONLY"
    return "TOO_SMALL_QUALITATIVE_REVIEW"


def analyse_group(ratings, cfg):
    """ratings: list of ints 1..5 for one comparison group."""
    n = len(ratings)
    counts = Counter(ratings)
    status = group_status(n, cfg)
    rows = []
    for rating, target_pct in sorted(cfg["guided_distribution"].items(), reverse=True):
        c = counts.get(rating, 0)
        actual_pct = c / n if n else 0.0
        lo, hi = binomial_interval(n, target_pct, cfg["dist_alert_confidence"]) if n else (0, 0)
        outside = not (lo <= c <= hi)
        rows.append({
            "rating": rating,
            "count": c,
            "actual_pct": actual_pct,
            "target_pct": target_pct,
            "variance_pp": (actual_pct - target_pct) * 100,
            "expected_range": (lo, hi),
            "flag": outside and status == "FULL_COMPARISON",
            "note": ("Outside expected range - committee review" if outside and status == "FULL_COMPARISON"
                     else "Outside range (indicative only)" if outside and status == "INDICATIVE_ONLY"
                     else ""),
        })
    return {"n": n, "status": status, "rows": rows,
            "prob_no_exceptional": (1 - cfg["guided_distribution"][5]) ** n if n else None}


def analyse_by(records, key, cfg, rating_field="rating"):
    groups = defaultdict(list)
    for r in records:
        groups[r[key]].append(r[rating_field])
    return {g: analyse_group(v, cfg) for g, v in sorted(groups.items())}
