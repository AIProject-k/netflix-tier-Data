"""Accumulate the full weekly TOP 10 history the N100 engine needs.

Netflix's public TSVs already carry every week back to mid-2021, so one run
backfills the whole history:

    data/history/global.json              all weeks, 4 worldwide lists
    data/history/countries/<CC>.json      all weeks, per tracked country

`data/latest/` is produced by build_data.py and is left untouched here.

Pure stdlib. Run: python scripts/build_history.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from build_data import (
    CATEGORY_SLUG,
    COUNTRIES_URL,
    GLOBAL_URL,
    ROOT,
    as_int,
    clean,
    fetch_tsv,
)
from n100.config import TRACKED_COUNTRIES
from n100.normalize import media_type

OUT_DIR = os.path.join(ROOT, "data", "history")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))


def build_global(rows: list[dict]) -> dict:
    out = []
    weeks = set()
    for r in rows:
        slug = CATEGORY_SLUG.get(r["category"].strip())
        if slug is None:
            continue
        weeks.add(r["week"])
        out.append(
            {
                "week": r["week"],
                "category": slug,
                "type": "film" if slug.startswith("films") else "tv",
                "lang": "non_english" if "non_english" in slug else "english",
                "rank": int(r["weekly_rank"]),
                "showTitle": r["show_title"].strip(),
                "seasonTitle": clean(r.get("season_title", "")),
                "hoursViewed": as_int(r.get("weekly_hours_viewed", "")),
                "views": as_int(r.get("weekly_views", "")),
                "cumWeeks": as_int(r.get("cumulative_weeks_in_top_10", "")) or 0,
            }
        )
    out.sort(key=lambda e: (e["week"], e["category"], e["rank"]))
    return {"generatedAt": _now(), "weekCount": len(weeks), "rows": out}


def build_country(rows: list[dict], code: str) -> dict:
    out = []
    weeks = set()
    for r in rows:
        if r["country_iso2"].strip().upper() != code:
            continue
        weeks.add(r["week"])
        out.append(
            {
                "week": r["week"],
                "type": media_type(r["category"]),
                "rank": int(r["weekly_rank"]),
                "showTitle": r["show_title"].strip(),
                "seasonTitle": clean(r.get("season_title", "")),
                "cumWeeks": as_int(r.get("cumulative_weeks_in_top_10", "")) or 0,
            }
        )
    out.sort(key=lambda e: (e["week"], e["type"], e["rank"]))
    return {
        "country": code,
        "generatedAt": _now(),
        "weekCount": len(weeks),
        "rows": out,
    }


def main() -> int:
    print("downloading global tsv ...")
    global_rows = fetch_tsv(GLOBAL_URL)
    print("downloading countries tsv (large, ~30 MB) ...")
    country_rows = fetch_tsv(COUNTRIES_URL)

    gpayload = build_global(global_rows)
    write_json(os.path.join(OUT_DIR, "global.json"), gpayload)
    print(f"global.json: {gpayload['weekCount']} weeks, {len(gpayload['rows'])} rows")

    for code in TRACKED_COUNTRIES:
        payload = build_country(country_rows, code)
        write_json(os.path.join(OUT_DIR, "countries", f"{code}.json"), payload)
        print(f"  {code}: {payload['weekCount']} weeks, {len(payload['rows'])} rows")

    print(f"wrote history -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
