"""Compute the N100 experimental TOP 100 for Korea from accumulated history.

Reads data/history/ (produced by build_history.py), applies score v1
(see docs/n100-score-v1.md), and writes data/n100/kr.json.

N100 is NOT an official Netflix ranking. It is our own estimate built only from
titles that actually charted in Netflix's public weekly TOP 10.

Pure stdlib. Run: python scripts/build_n100.py   (after build_history.py)
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

from build_data import ROOT
from n100 import score
from n100.config import (
    FORMULA_VERSION,
    MOMENTUM_LOOKBACK,
    N100_COUNTRY,
    TOP_N,
    TRACKED_COUNTRIES,
    WEIGHTS,
    WINDOW_WEEKS,
)
from n100.normalize import display_title, key_of

HISTORY_DIR = os.path.join(ROOT, "data", "history")
OUT_PATH = os.path.join(ROOT, "data", "n100", "kr.json")


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build() -> dict:
    subject = load(os.path.join(HISTORY_DIR, "countries", f"{N100_COUNTRY}.json"))
    tracked = {
        cc: load(os.path.join(HISTORY_DIR, "countries", f"{cc}.json"))
        for cc in TRACKED_COUNTRIES
    }
    global_hist = load(os.path.join(HISTORY_DIR, "global.json"))

    all_weeks = sorted({r["week"] for r in subject["rows"]}, reverse=True)
    if not all_weeks:
        raise SystemExit(f"no {N100_COUNTRY} history rows")
    window = all_weeks[:WINDOW_WEEKS]
    ref_week = window[0]
    week_index = {w: i for i, w in enumerate(window)}  # 0 = reference week

    # --- gather per-content facts inside the window --------------------------
    appearances: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    points_recent: dict[tuple, dict[int, int]] = defaultdict(dict)
    peak_cum: dict[tuple, int] = defaultdict(int)
    spellings: dict[tuple, Counter] = defaultdict(Counter)
    seasons: dict[tuple, set] = defaultdict(set)
    week_rank: dict[tuple, dict[int, int]] = defaultdict(dict)  # weeks_ago -> rank

    for r in subject["rows"]:
        wi = week_index.get(r["week"])
        if wi is None:
            continue
        k = key_of(r["showTitle"], r["type"])
        rank = r["rank"]
        appearances[k].append((wi, rank))
        week_rank[k][wi] = rank
        if wi <= MOMENTUM_LOOKBACK:
            points_recent[k][wi] = score.rank_points(rank)
        peak_cum[k] = max(peak_cum[k], r.get("cumWeeks") or 0)
        spellings[k][display_title(r["showTitle"])] += 1
        if r.get("seasonTitle"):
            seasons[k].add(r["seasonTitle"])

    # --- global spread signal for the reference week -----------------------
    charting_ref: dict[str, set] = {}
    for cc, hist in tracked.items():
        charting_ref[cc] = {
            key_of(r["showTitle"], r["type"]) for r in hist["rows"] if r["week"] == ref_week
        }
    global_ref = {
        key_of(r["showTitle"], r["type"]) for r in global_hist["rows"] if r["week"] == ref_week
    }

    # --- score every candidate ------------------------------------------
    entries = []
    for k, apps in appearances.items():
        _, mtype = k
        last_wi = min(wi for wi, _ in apps)
        first_wi = max(wi for wi, _ in apps)
        last_rank = week_rank[k][last_wi]
        prev_rank = week_rank[k].get(last_wi + 1)
        countries_charting = sum(1 for cc in TRACKED_COUNTRIES if k in charting_ref.get(cc, ()))

        components = {
            "rank": score.rank_score(apps),
            "recency": score.recency_score(apps),
            "longevity": score.longevity_score(peak_cum[k]),
            "momentum": score.momentum_score(points_recent[k]),
            "global": score.global_score(countries_charting, len(TRACKED_COUNTRIES), k in global_ref),
        }
        entries.append(
            {
                "title": spellings[k].most_common(1)[0][0],
                "type": mtype,
                "score": round(score.combine(components), 2),
                "components": {name: round(v, 1) for name, v in components.items()},
                "weeksCharted": len(apps),
                "peakRank": min(rank for _, rank in apps),
                "lastWeek": window[last_wi],
                "lastRank": last_rank,
                "prevRank": prev_rank,
                "delta": (prev_rank - last_rank) if prev_rank is not None else None,
                "firstSeenInWindow": window[first_wi],
                "countriesCharting": countries_charting,
            }
        )

    entries.sort(key=lambda e: e["score"], reverse=True)

    def ranked(items: list[dict]) -> list[dict]:
        return [dict(e, rank=i + 1) for i, e in enumerate(items[:TOP_N])]

    films = [e for e in entries if e["type"] == "film"]
    tv = [e for e in entries if e["type"] == "tv"]

    collapsed = sum(1 for k in seasons if len(seasons[k]) > 1)

    return {
        "generatedAt": _now(),
        "formulaVersion": FORMULA_VERSION,
        "notOfficial": "Estimated by N100 from Netflix's public weekly TOP 10. Not a Netflix ranking.",
        "country": N100_COUNTRY,
        "referenceWeek": ref_week,
        "window": {"weeks": WINDOW_WEEKS, "present": len(window), "from": window[-1], "to": ref_week},
        "weights": WEIGHTS,
        "pool": {"films": len(films), "tv": len(tv), "total": len(entries), "seasonsCollapsed": collapsed},
        "all": ranked(entries),
        "films": ranked(films),
        "tv": ranked(tv),
    }


def main() -> int:
    payload = build()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    p = payload["pool"]
    w = payload["window"]
    print(f"reference week : {payload['referenceWeek']}")
    print(f"window         : {w['from']} .. {w['to']}  ({w['present']}/{w['weeks']} weeks present)")
    print(f"KR pool        : films={p['films']}  tv={p['tv']}  total={p['total']}")
    print(f"seasons merged : {p['seasonsCollapsed']} contents charted under >1 season label")
    for name in ("all", "films", "tv"):
        fills = "fills TOP 100" if len(payload[name]) >= TOP_N else f"only {len(payload[name])}"
        print(f"  {name:5s}: {fills}")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
