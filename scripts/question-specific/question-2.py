"""
Q2: how are the shares of the grades by NTA and borough?

Reads data/interim/inspections.csv, takes each restaurant's current grade (current_grades in
common.py, the same definition as Q4) and counts the grade cards by NTA and borough
Run from the repo root: python3 scripts/question-specific/question-2.py
"""

import json
from pathlib import Path

import pandas as pd

from common import CARDS, OUT_DIR, current_grades, read, snapshot

NTA_OUT_FILE = Path("src/data/q2-nta.csv")
BORO_OUT_FILE = Path("src/data/q2-boro.csv")
SUMMARY_OUT_FILE = OUT_DIR / "q2-summary.json"
NTA_NAMES_FILE = Path("data/reference/nta-2010.csv")  # from scripts/download-nta-lookup.py
MIN_RESTAURANTS = 20  # an NTA with fewer restaurants is gray on the map: its shares are too noisy

inspections = read("inspections")
restaurants = read("restaurants")
print(f"Read {len(inspections):,} inspections")

# One row per restaurant: the grade of its most recent graded inspection, and the card it posts.
# N becomes "Not Yet Graded", Z and P become "Grade Pending", like the cards in the window
by_restaurant = current_grades(inspections)

restaurants_with_no_grade = len(restaurants) - len(by_restaurant)

print(f"Restaurants with no grade: {restaurants_with_no_grade}")

grade_counts = by_restaurant["card"].value_counts()

print(grade_counts)
print(f"Total: {grade_counts.sum():,}")

# Attach each restaurant's neighborhood (2010 NTA code) and borough
by_restaurant = by_restaurant.merge(
    restaurants[["camis", "nta", "boro"]], on="camis", how="left", validate="one_to_one"
)

# Restaurants without an NTA can't go on the map. We drop them from both the NTA and the
# borough tables, so each borough total is exactly the sum of its neighborhoods
no_nta = by_restaurant["nta"].fillna("") == ""
print(f"Restaurants with no NTA (excluded): {no_nta.sum():,}")
by_restaurant = by_restaurant[~no_nta].copy()

# Take the borough from the NTA code prefix instead of the "boro" column. They disagree
# only in Marble Hill (MN01): legally Manhattan, but its mailing addresses say Bronx.
# Using the prefix keeps borough totals consistent with the map
PREFIX_TO_BORO = {
    "MN": "Manhattan",
    "BX": "Bronx",
    "BK": "Brooklyn",
    "QN": "Queens",
    "SI": "Staten Island",
}
nta_boro = by_restaurant["nta"].str[:2].map(PREFIX_TO_BORO)
changed = by_restaurant["boro"] != nta_boro
print(f"Restaurants whose borough changed to match the NTA: {changed.sum():,}")
by_restaurant["boro"] = nta_boro

# Check: no unknown prefixes, and every NTA now sits inside a single borough
assert by_restaurant["boro"].notna().all(), "unknown NTA prefix"
boros_per_nta = by_restaurant.groupby("nta")["boro"].nunique()
assert boros_per_nta.max() == 1, "an NTA spans two boroughs"
print(f"Restaurants on the map: {len(by_restaurant):,} in {len(boros_per_nta)} NTAs")

# Count restaurants per NTA and grade group: one row per NTA, one column per grade.
# The page computes the shares, so we store counts only
GROUP_COLUMNS = dict(zip(CARDS, ["count_A", "count_B", "count_C", "count_grade_pending", "count_not_graded"]))
nta_counts = (
    pd.crosstab([by_restaurant["nta"], by_restaurant["boro"]], by_restaurant["card"])
        .reindex(columns=list(GROUP_COLUMNS), fill_value=0)  # keep all four columns even if a group is empty
        .rename(columns=GROUP_COLUMNS)
        .rename_axis(columns=None)
        .reset_index()
)
nta_counts["total_count"] = nta_counts[list(GROUP_COLUMNS.values())].sum(axis=1)

# Add every 2010 NTA with its name, so each shape on the map has a row (NTAs without
# restaurants get zeros)
nta_names = pd.read_csv(NTA_NAMES_FILE, dtype=str)
unknown = set(nta_counts["nta"]) - set(nta_names["nta"])
assert not unknown, f"NTA codes missing from {NTA_NAMES_FILE}: {unknown}"
nta_counts = nta_names.merge(nta_counts, on="nta", how="left", validate="one_to_one")
nta_counts["boro"] = nta_counts["boro"].fillna(nta_counts["nta"].str[:2].map(PREFIX_TO_BORO))
count_columns = list(GROUP_COLUMNS.values()) + ["total_count"]
nta_counts[count_columns] = nta_counts[count_columns].fillna(0).astype(int)

# Why an NTA is gray on the map instead of colored by its shares (blank if it is colored).
# Parks and cemeteries come first: their few restaurants are concessions, not a neighborhood
is_park = nta_counts["nta_name"].str.startswith("park-cemetery-etc")
too_few = nta_counts["total_count"] < MIN_RESTAURANTS
nta_counts["gray_reason"] = ""
nta_counts.loc[too_few, "gray_reason"] = f"fewer than {MIN_RESTAURANTS} restaurants"
nta_counts.loc[is_park, "gray_reason"] = "park or cemetery"
print(nta_counts["gray_reason"].replace("", "(colored)").value_counts().to_string())

# Check: every restaurant on the map is counted exactly once
assert nta_counts["total_count"].sum() == len(by_restaurant), "NTA totals don't add up"
print(f"NTA table: {len(nta_counts)} rows, {nta_counts['total_count'].sum():,} restaurants")
print(nta_counts.sort_values("total_count", ascending=False).head())

# Borough table: add up the NTA rows inside each borough, so it matches the map exactly
boro_counts = nta_counts.groupby("boro", as_index=False)[count_columns].sum()

# Check: borough totals add up to the same number of restaurants as the NTA table
assert boro_counts["total_count"].sum() == nta_counts["total_count"].sum(), "borough totals don't add up"
print(boro_counts)

NTA_OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
nta_counts.sort_values("nta").to_csv(NTA_OUT_FILE, index=False)
boro_counts.to_csv(BORO_OUT_FILE, index=False)
print(f"Wrote {NTA_OUT_FILE} ({len(nta_counts)} rows) and {BORO_OUT_FILE} ({len(boro_counts)} rows)")

# Who is on the map and who is left out, for the labels next to the map
gray = nta_counts["gray_reason"] != ""
summary = {
    "snapshot": snapshot(),
    "restaurants": len(restaurants),
    "never_graded": restaurants_with_no_grade,
    "with_grade": int(grade_counts.sum()),
    "no_nta": int(no_nta.sum()),
    "on_map": len(by_restaurant),
    "borough_changed": int(changed.sum()),
    "ntas": len(nta_counts),
    "min_restaurants": MIN_RESTAURANTS,
    "ntas_colored": int((~gray).sum()),
    "ntas_gray_park": int(is_park.sum()),
    "ntas_gray_too_few": int((too_few & ~is_park).sum()),
    "restaurants_in_gray_ntas": int(nta_counts.loc[gray, "total_count"].sum()),
}
assert summary["with_grade"] == summary["on_map"] + summary["no_nta"], "restaurants lost on the way"
SUMMARY_OUT_FILE.write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))