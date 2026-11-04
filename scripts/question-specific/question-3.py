"""
Q3: how much do scores differ by cuisine?

Reads data/interim/inspections.csv and data/interim/restaurants.csv and writes src/data/q3-cuisines.csv
with the box plot numbers (count, quartiles, whiskers) of first-inspection scores for the 20 most common cuisines
"""

from pathlib import Path

import pandas as pd

IN_FILE = Path("data/interim/inspections.csv")
RESTAURANTS_FILE = Path("data/interim/restaurants.csv")
OUT_FILE = Path("src/data/q3-cuisines.csv")
FIRST_INSPECTION = "Cycle Inspection / Initial Inspection"
TOP_N = 20

inspections = pd.read_csv(IN_FILE, dtype={"camis": str})
restaurants = pd.read_csv(RESTAURANTS_FILE, dtype={"camis": str})
print(f"Read {len(inspections):,} inspections")

# 1. Keep only first inspections with a score, same as Q1
first = inspections[inspections["inspection_type"] == FIRST_INSPECTION].copy()
first = first.dropna(subset=["score"])
first["score"] = first["score"].astype(int)

# 2. Attach each restaurant's cuisine
first = first.merge(
    restaurants[["camis", "cuisine_description"]], on="camis", how="left", validate="many_to_one"
)
no_cuisine = first["cuisine_description"].isna()
print(f"First inspections with no cuisine (excluded): {no_cuisine.sum():,}")
first = first[~no_cuisine].rename(columns={"cuisine_description": "cuisine"})

# 3. Keep the 20 cuisines with the most first inspections
top = first["cuisine"].value_counts().head(TOP_N).index
first = first[first["cuisine"].isin(top)]
print(f"Kept {len(first):,} first inspections in the top {TOP_N} cuisines")

# 4. Count and quartiles per cuisine
stats = first.groupby("cuisine")["score"].agg(
    count="size",
    percentile_25=lambda s: s.quantile(0.25),
    median="median",
    percentile_75=lambda s: s.quantile(0.75),
)

# 5. Whiskers: the furthest real scores that are still within 1.5 * interquartile range of the box
def whiskers(s):
    percentile_25, percentile_75 = s.quantile(0.25), s.quantile(0.75)
    interquartile_range = percentile_75 - percentile_25
    inside = s[(s >= percentile_25 - 1.5 * interquartile_range) & (s <= percentile_75 + 1.5 * interquartile_range)]
    return pd.Series({"whisker_low": inside.min(), "whisker_high": inside.max()})

stats = stats.join(first.groupby("cuisine")["score"].apply(whiskers).unstack())
stats[["whisker_low", "whisker_high"]] = stats[["whisker_low", "whisker_high"]].astype(int)

# Check: every kept inspection is counted once
assert stats["count"].sum() == len(first), "cuisine counts don't add up"

# 6. Sort by median (ties by count) and save
stats = stats.sort_values(["median", "count"], ascending=[True, False]).reset_index()
print(stats.to_string(index=False))

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
stats.to_csv(OUT_FILE, index=False)
print(f"Wrote {OUT_FILE}: {len(stats)} rows, {stats['count'].sum():,} inspections")
