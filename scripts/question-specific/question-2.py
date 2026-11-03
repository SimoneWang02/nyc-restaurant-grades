"""
Q2: how are the shares of the grades by NTA and borough?

Reads data/interim/inspections.csv, for each restaurant keep the most recent inspection grade and group by NTA and borough
"""

from pathlib import Path

import pandas as pd

IN_FILE = Path("data/interim/inspections.csv")
NTA_OUT_FILE = Path("src/data/q2-nta.csv")
BORO_OUT_FILE = Path("src/data/q2-boro.csv")
RESTAURANTS_FILE = Path("data/interim/restaurants.csv")

inspections = pd.read_csv(IN_FILE, dtype={"camis": str})
restaurants = pd.read_csv(RESTAURANTS_FILE, dtype={"camis": str})
print(f"Read {len(inspections):,} inspections")

# Remove rows with NaN grades and sort by "inspection_date"
inspections = inspections.dropna(subset=["grade"]).sort_values("inspection_date", kind="stable")

# Group by "camis" and keep last inspection grade
by_restaurant = inspections.groupby("camis").tail(1).copy()

restaurants_with_no_grade = len(restaurants) - len(by_restaurant)

print(f"Restaurants with no grade: {restaurants_with_no_grade}")

# N (not yet graded), Z (grade pending) and P (pending, issued at reopening) all mean the restaurant has no letter grade yet, so they become one "Pending" group
PENDING = {"N": "Pending", "Z": "Pending", "P": "Pending"}
by_restaurant["grade_group"] = by_restaurant["grade"].replace(PENDING)

grade_counts = by_restaurant["grade_group"].value_counts()

print(grade_counts)
print(f"Total: {grade_counts.sum():,}")

# Attach each restaurant's neighborhood (2010 NTA code) and borough
by_restaurant = by_restaurant.merge(
    restaurants[["camis", "nta", "boro"]], on="camis", how="left", validate="one_to_one"
)

# Restaurants without an NTA can't go on the map. We drop them from both the NTA and the
# borough tables, so each borough total is exactly the sum of its neighborhoods
no_nta = by_restaurant["nta"].isna()
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
GROUP_COLUMNS = {"A": "count_A", "B": "count_B", "C": "count_C", "Pending": "count_pending"}
nta_counts = (
    pd.crosstab([by_restaurant["nta"], by_restaurant["boro"]], by_restaurant["grade_group"])
        .reindex(columns=list(GROUP_COLUMNS), fill_value=0)  # keep all four columns even if a group is empty
        .rename(columns=GROUP_COLUMNS)
        .rename_axis(columns=None)
        .reset_index()
)
nta_counts["total_count"] = nta_counts[list(GROUP_COLUMNS.values())].sum(axis=1)

# Check: every restaurant on the map is counted exactly once
assert nta_counts["total_count"].sum() == len(by_restaurant), "NTA totals don't add up"
print(f"NTA table: {len(nta_counts)} rows, {nta_counts['total_count'].sum():,} restaurants")
print(nta_counts.sort_values("total_count", ascending=False).head())

# Borough table: add up the NTA rows inside each borough, so it matches the map exactly
count_columns = list(GROUP_COLUMNS.values()) + ["total_count"]
boro_counts = nta_counts.groupby("boro", as_index=False)[count_columns].sum()

# Check: borough totals add up to the same number of restaurants as the NTA table
assert boro_counts["total_count"].sum() == nta_counts["total_count"].sum(), "borough totals don't add up"
print(boro_counts)

NTA_OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
nta_counts.sort_values("nta").to_csv(NTA_OUT_FILE, index=False)
boro_counts.to_csv(BORO_OUT_FILE, index=False)
print(f"Wrote {NTA_OUT_FILE} ({len(nta_counts)} rows) and {BORO_OUT_FILE} ({len(boro_counts)} rows)")