"""
Q3: how much do scores differ by cuisine?

Reads data/interim/inspections.csv and data/interim/restaurants.csv, keeps the routine first
inspections in the shared time window (START to END in common.py, the same as Q1, Q5 and Q6)
and writes:
    src/data/q3-cuisines.csv    box plot numbers (count, quartiles, whiskers, outliers) of
                                first-inspection scores for every cuisine with at least
                                MIN_COUNT first inspections
    src/data/q3-summary.json    window, snapshot and the counts quoted in the page text
Run from the repo root: python3 scripts/question-specific/question-3.py
"""

import json

import pandas as pd

from common import END, FIRST_INSPECTION, OUT_DIR, START, read, save, snapshot

MIN_COUNT = 50  # enough first inspections for a box; the page colors each box by its count
# Categories that are not a cuisine, so they don't belong in a comparison of cuisines
NOT_CUISINES = {"Other", "Bottled Beverages"}

inspections = read("inspections")
restaurants = read("restaurants")
print(f"Read {len(inspections):,} inspections")

# 1. Keep only first inspections in the time window that have a score, same as Q1
first = inspections[inspections["inspection_type"] == FIRST_INSPECTION]
in_window = first["inspection_date"].between(START, END)
no_score = first["score"] == ""
print(f"{(~in_window).sum():,} first inspections before {START} left out, "
      f"{(in_window & no_score).sum():,} without a score left out")
first = first[in_window & ~no_score].copy()
first["score"] = first["score"].astype(float).astype(int)
in_window_count = len(first)

# 2. Attach each restaurant's cuisine
first = first.merge(
    restaurants[["camis", "cuisine_description"]], on="camis", how="left", validate="many_to_one"
)
first = first.rename(columns={"cuisine_description": "cuisine"})
no_cuisine = first["cuisine"].fillna("") == ""
print(f"First inspections with no cuisine (excluded): {no_cuisine.sum():,}")
first = first[~no_cuisine]

# 3. Drop the non-cuisine categories, then keep cuisines with at least MIN_COUNT first inspections
not_cuisine = first["cuisine"].isin(NOT_CUISINES)
print(f"First inspections in {sorted(NOT_CUISINES)} (excluded): {not_cuisine.sum():,}")
first = first[~not_cuisine]
counts = first["cuisine"].value_counts()
kept = counts[counts >= MIN_COUNT].index
small = ~first["cuisine"].isin(kept)
print(f"{(counts < MIN_COUNT).sum()} cuisines with fewer than {MIN_COUNT} first inspections "
      f"({small.sum():,} inspections) left out")
first = first[~small]
print(f"Kept {len(first):,} first inspections in {len(kept)} cuisines with at least {MIN_COUNT} each")

# 4. Count, restaurants and quartiles per cuisine. A restaurant can have more than one first
# inspection in the window (one per cycle), so "restaurants" is smaller than "count"
stats = first.groupby("cuisine")["score"].agg(
    count="size",
    percentile_25=lambda s: s.quantile(0.25),
    median="median",
    percentile_75=lambda s: s.quantile(0.75),
)
stats["restaurants"] = first.groupby("cuisine")["camis"].nunique()

# 5. Whiskers: the furthest real scores that are still within 1.5 * interquartile range of the box.
# The scores past the whiskers (outliers) are not drawn, so we count them and keep the highest one.
# Only high outliers exist: the lower limit is below 0 for every cuisine, and no score is below 0
def whiskers(s):
    percentile_25, percentile_75 = s.quantile(0.25), s.quantile(0.75)
    interquartile_range = percentile_75 - percentile_25
    low_limit = percentile_25 - 1.5 * interquartile_range
    high_limit = percentile_75 + 1.5 * interquartile_range
    inside = s[(s >= low_limit) & (s <= high_limit)]
    return pd.Series({
        "whisker_low": inside.min(),
        "whisker_high": inside.max(),
        "outliers_low": (s < low_limit).sum(),
        "outliers": (s > high_limit).sum(),
        "max_score": s.max(),
    })

whisker_columns = ["whisker_low", "whisker_high", "outliers", "max_score"]
stats = stats.join(first.groupby("cuisine")["score"].apply(whiskers).unstack())
stats[whisker_columns + ["outliers_low"]] = stats[whisker_columns + ["outliers_low"]].astype(int)

# Check: every kept inspection is counted once, and there are no low outliers to show
assert stats["count"].sum() == len(first), "cuisine counts don't add up"
assert stats["outliers_low"].sum() == 0, "some cuisine has low outliers: add them to the page"
assert (stats["max_score"] >= stats["whisker_high"]).all(), "a whisker is past the highest score"

# 6. Sort by median (ties by count) and save
stats = stats.sort_values(["median", "count"], ascending=[True, False]).reset_index()
stats = stats[["cuisine", "count", "restaurants", "percentile_25", "median", "percentile_75"] + whisker_columns]
print(stats.to_string(index=False))
save(stats, "q3-cuisines.csv")

# 7. The numbers the page quotes
outliers = stats["outliers"].sum()
summary = {
    "snapshot": snapshot(),
    "start": START,
    "end": END,
    "min_count": MIN_COUNT,
    "inspections_in_window": in_window_count,
    "no_cuisine_left_out": int(no_cuisine.sum()),
    "not_cuisine_left_out": int(not_cuisine.sum()),
    "small_cuisines": int((counts < MIN_COUNT).sum()),
    "small_cuisines_left_out": int(small.sum()),
    "cuisines": len(stats),
    "inspections": int(stats["count"].sum()),
    "restaurants": int(first["camis"].nunique()),
    "outliers": int(outliers),
    "share_outliers": round(float(outliers) / len(first), 6),
}
assert summary["inspections_in_window"] == (summary["no_cuisine_left_out"] + summary["not_cuisine_left_out"]
                                            + summary["small_cuisines_left_out"] + summary["inspections"]), \
    "inspections lost on the way"
(OUT_DIR / "q3-summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
