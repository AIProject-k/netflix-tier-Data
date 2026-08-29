"""Netflix Tudum Top 10 -> compact per-country JSON.

Downloads the two official TSV files, keeps only the most recent week, and
writes small JSON files the Android app fetches from GitHub raw:

    data/latest/index.json              week + country list
    data/latest/global.json             global top 10 (4 categories)
    data/latest/countries/<ISO2>.json   per-country top 10 (films + tv)

Pure stdlib, no dependencies. Run: python scripts/build_data.py
"""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

BASE = "https://www.netflix.com/tudum/top10/data"
GLOBAL_URL = f"{BASE}/all-weeks-global.tsv"
COUNTRIES_URL = f"{BASE}/all-weeks-countries.tsv"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "latest")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NetflixTierBot/1.0"

CATEGORY_SLUG = {
    "Films (English)": "films_english",
    "Films (Non-English)": "films_non_english",
    "TV (English)": "tv_english",
    "TV (Non-English)": "tv_non_english",
}


def _download_curl(url: str) -> str:
    out = subprocess.run(
        ["curl", "-sSL", "--fail", "--retry", "3", "-A", UA, url],
        capture_output=True,
        timeout=300,
    )
    if out.returncode != 0:
        raise RuntimeError(f"curl exited {out.returncode}: {out.stderr.decode(errors='replace')[:300]}")
    return out.stdout.decode("utf-8", errors="replace")


def _download_urllib(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept-Encoding": "identity"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_tsv(url: str) -> list[dict]:
    # Netflix's CDN trips urllib's IncompleteRead on these files; curl is reliable.
    downloaders = []
    if shutil.which("curl"):
        downloaders.append(_download_curl)
    downloaders.append(_download_urllib)

    last_err: Exception | None = None
    for download in downloaders:
        try:
            raw = download(url)
            rows = list(csv.DictReader(io.StringIO(raw), delimiter="\t"))
            if not rows:
                raise RuntimeError("empty response")
            return rows
        except Exception as err:  # noqa: BLE001 - fall through to next downloader
            last_err = err
            print(f"  {download.__name__} failed: {err}")
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def as_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value or value.upper() == "N/A":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def as_float(value: str) -> float | None:
    value = (value or "").strip()
    if not value or value.upper() == "N/A":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def clean(value: str) -> str | None:
    value = (value or "").strip()
    if not value or value.upper() == "N/A":
        return None
    return value


def latest_week(rows: list[dict]) -> str:
    return max(r["week"] for r in rows)


def build_global(rows: list[dict], week: str) -> dict:
    categories: dict[str, list[dict]] = {slug: [] for slug in CATEGORY_SLUG.values()}
    for r in rows:
        if r["week"] != week:
            continue
        slug = CATEGORY_SLUG.get(r["category"].strip())
        if slug is None:
            continue
        categories[slug].append(
            {
                "rank": int(r["weekly_rank"]),
                "title": r["show_title"].strip(),
                "season": clean(r.get("season_title", "")),
                "hoursViewed": as_int(r.get("weekly_hours_viewed", "")),
                "views": as_int(r.get("weekly_views", "")),
                "runtime": as_float(r.get("runtime", "")),
                "weeksInTop10": as_int(r.get("cumulative_weeks_in_top_10", "")) or 0,
            }
        )
    for entries in categories.values():
        entries.sort(key=lambda e: e["rank"])
    return {"week": week, "categories": categories}


def build_countries(rows: list[dict], week: str) -> tuple[dict, list[dict]]:
    by_country: dict[str, dict] = {}
    for r in rows:
        if r["week"] != week:
            continue
        code = r["country_iso2"].strip().upper()
        name = r["country_name"].strip()
        bucket = by_country.setdefault(
            code, {"code": code, "name": name, "films": [], "tv": []}
        )
        entry = {
            "rank": int(r["weekly_rank"]),
            "title": r["show_title"].strip(),
            "season": clean(r.get("season_title", "")),
            "weeksInTop10": as_int(r.get("cumulative_weeks_in_top_10", "")) or 0,
        }
        key = "films" if r["category"].strip() == "Films" else "tv"
        bucket[key].append(entry)

    index_countries = []
    for code in sorted(by_country, key=lambda c: by_country[c]["name"]):
        bucket = by_country[code]
        bucket["films"].sort(key=lambda e: e["rank"])
        bucket["tv"].sort(key=lambda e: e["rank"])
        index_countries.append({"code": code, "name": bucket["name"]})
    return by_country, index_countries


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    print("downloading global tsv ...")
    global_rows = fetch_tsv(GLOBAL_URL)
    print("downloading countries tsv (large, ~30 MB) ...")
    country_rows = fetch_tsv(COUNTRIES_URL)

    week = max(latest_week(global_rows), latest_week(country_rows))
    print(f"latest week: {week}")

    global_payload = build_global(global_rows, week)
    countries, index_countries = build_countries(country_rows, week)

    write_json(os.path.join(OUT_DIR, "global.json"), global_payload)
    for code, bucket in countries.items():
        write_json(
            os.path.join(OUT_DIR, "countries", f"{code}.json"),
            {
                "week": week,
                "country": {"code": code, "name": bucket["name"]},
                "films": bucket["films"],
                "tv": bucket["tv"],
            },
        )
    write_json(
        os.path.join(OUT_DIR, "index.json"),
        {
            "week": week,
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "globalCategories": list(CATEGORY_SLUG.values()),
            "countries": index_countries,
        },
    )
    print(f"wrote global.json + {len(countries)} country files + index.json -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
