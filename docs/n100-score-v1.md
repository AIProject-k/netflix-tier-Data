# N100 Score — v1

**N100 is not an official Netflix ranking.** It is our own estimate of a
"beyond TOP 10" chart, built only from titles that actually appeared in
Netflix's public weekly TOP 10.

- Subject: Korea (`N100_COUNTRY = "KR"`)
- Candidate pool: every content that charted in KR's weekly Films **or** TV
  TOP 10 at least once in the last `WINDOW_WEEKS` (26) chart weeks.
- Output: `data/n100/kr.json` — three ranked lists (`all`, `films`, `tv`),
  each capped at `TOP_N` (100).
- All constants: `scripts/n100/config.py`. Change them and re-run
  `build_n100.py` — no re-download needed (it reads `data/history/`).

## Content identity

Netflix already separates the franchise root (`show_title`) from the season
(`season_title`), so `"Squid Game"` S2 and S3 both arrive as
`show_title = "Squid Game"`. The grouping key is therefore just
`(whitespace-normalized casefolded show_title, media_type)` where `media_type`
is `film` or `tv`. In the current 26-week KR data only **4** contents ever
charted under more than one season label, so this is enough for v1.

## The five components

Each returns **0–100**; the final score is their weighted sum.

| Component | Weight | Definition |
|---|---|---|
| Rank | 40% | Mean of `RANK_POINTS[rank]` over every weekly appearance in the window. `RANK_POINTS`: 1→100, 2→90, 3→82, 4→75, 5→68, 6→61, 7→54, 8→47, 9→40, 10→33 (1st is worth far more than a linear `10 − rank`). |
| Recency | 20% | `DECAY_WEEKLY[weeksAgo] × 100` for the **most recent** appearance. `DECAY_WEEKLY`: 0w→1.00, 1w→0.88, 2w→0.77, 3w→0.68, 4w→0.60, 5w→0.53, 6w→0.46 … floor `0.12`. A title still charting this week scores 100; one last seen 5 weeks ago scores 53. |
| Longevity | 15% | Peak `cumulative_weeks_in_top_10` seen for the title, mapped via `LONGEVITY_BONUS` (1w→0, 2w→3, 3w→6, 4w→9, 6w→13, 8w→15, 12w+→20), then scaled `bonus / 20 × 100`. Separates one-hit wonders from long runs. |
| Momentum | 15% | `thisWeekPoints − avg(previous 3 weeks' points)`, where points are `RANK_POINTS[rank]` (0 for a week the title was absent). Mapped `clamp(50 + delta/2, 0, 100)`: flat → 50, strong climb → up to 100, drop → down to 0. A brand-new hot entry compares against 0 and scores high. |
| Global | 10% | `(countriesCharting / 10) × 80 + (20 if in any worldwide TOP 10 that week)`, for the reference week. `countriesCharting` = how many of the 10 tracked countries (KR, US, JP, GB, BR, MX, FR, DE, IN, TW) had the title in TOP 10. A KR-only hit scores 8; a worldwide phenomenon approaches 100. |

```
N100 = 0.40·Rank + 0.20·Recency + 0.15·Longevity + 0.15·Momentum + 0.10·Global
```

Sorted descending, ranked 1..N, capped at 100. `films` and `tv` are the same
computation filtered by media type and re-ranked.

## Per-entry extras (for the future detail view)

`weeksCharted`, `peakRank`, `lastWeek`, `lastRank`, `prevRank`, `delta`
(`prevRank − lastRank`, positive = climbed), `firstSeenInWindow`,
`countriesCharting`, plus the `components` breakdown.

## Known v1 limitations (revisit before calling it done)

1. **TV pool < 100.** KR TV TOP 10 is dominated by long runs, so a 26-week
   window yields only ~80 unique series. Options: widen the window (40w), or
   publish a shorter TV list.
2. **Recency barely differentiates the top.** Almost every high-ranked title
   also charted in the reference week (Recency 100). It only bites for titles
   that dropped off. Acceptable, but the 20% weight is doing little work near
   the top.
3. **Global signal is coarse** — only 10 countries, only the reference week.
   Fine as a 10% tiebreaker, not a real "worldwide popularity" measure.
4. **No external signals** (search, social, IMDb) by design. If added later,
   show them as separate indicators next to the N100 rank, not folded into it.
