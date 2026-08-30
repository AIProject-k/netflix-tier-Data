"""All tunable constants for the N100 experimental ranking (formula v1).

Nothing here is "official". These numbers are a starting point chosen to be
explainable; expect to revise them once real data exposes problems.
"""

# Countries whose weekly TOP 10 history we accumulate. KR is the subject;
# the other nine feed the "global spread" signal.
TRACKED_COUNTRIES = ["KR", "US", "JP", "GB", "BR", "MX", "FR", "DE", "IN", "TW"]

# Which country the N100 TOP 100 is computed for.
N100_COUNTRY = "KR"

# How many of the most recent weekly charts form the candidate pool + scoring window.
WINDOW_WEEKS = 26

# Length of every published list (ALL / Films / Series). Fewer if the pool is smaller.
TOP_N = 100

# --- Rank Score (40%) -------------------------------------------------------
# Points for finishing a week at a given Netflix rank. 1st is worth much more
# than a linear 10 - rank would give.
RANK_POINTS = {1: 100, 2: 90, 3: 82, 4: 75, 5: 68, 6: 61, 7: 54, 8: 47, 9: 40, 10: 33}

# --- Recency (20%) --------------------------------------------------------
# Multiplier by how many chart weeks ago the title last appeared (index 0 = the
# reference week). Anything older than the table uses DECAY_FLOOR.
DECAY_WEEKLY = [1.00, 0.88, 0.77, 0.68, 0.60, 0.53, 0.46, 0.40,
                0.35, 0.30, 0.26, 0.22, 0.19, 0.17, 0.15]
DECAY_FLOOR = 0.12

# --- Longevity (15%) -----------------------------------------------------
# Bonus by peak cumulative-weeks-in-top-10 seen for the title. Scaled to 0..100
# against LONGEVITY_MAX before weighting.
LONGEVITY_BONUS = {1: 0, 2: 3, 3: 6, 4: 9, 5: 11, 6: 13, 7: 14,
                    8: 15, 9: 16, 10: 17, 11: 18, 12: 20}
LONGEVITY_MAX = 20

# --- Momentum (15%) ----------------------------------------------------
# Compares this week's rank points to the average of the previous
# MOMENTUM_LOOKBACK weeks. Flat -> 50, strong rise -> up to 100, fall -> down to 0.
MOMENTUM_LOOKBACK = 3

# --- Global (10%) ------------------------------------------------------
# globalScore = (countriesCharting / len(TRACKED_COUNTRIES)) * GLOBAL_SPREAD_MAX
#               + (GLOBAL_TOP10_BONUS if in any worldwide TOP 10 that week)
GLOBAL_SPREAD_MAX = 80
GLOBAL_TOP10_BONUS = 20

# --- Final blend -------------------------------------------------------
WEIGHTS = {"rank": 0.40, "recency": 0.20, "longevity": 0.15, "momentum": 0.15, "global": 0.10}

FORMULA_VERSION = "v1"
