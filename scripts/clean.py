"""
Clean the raw snapshot and split it into three tables.

Run from the repo root:  python3 scripts/clean.py

Reads the newest data/raw/inspections_*.csv (one row per violation) and writes:
    data/interim/restaurants.csv   one row per restaurant (CAMIS)
    data/interim/inspections.csv   one row per inspection (CAMIS + date + type)
    data/interim/violations.csv    one row per cited violation
"""

from pathlib import Path

import pandas as pd

OUT_DIR = Path("data/interim")
PLACEHOLDER_DATE = "01/01/1900"  # restaurants that have not been inspected yet

raw = sorted(Path("data/raw").glob("inspections_*.csv"))[-1]
df = pd.read_csv(raw, dtype=str)
print(f"Using {raw.name}: {len(df):,} rows, {df['CAMIS'].nunique():,} restaurants")

# Shorter snake_case names, e.g. "INSPECTION DATE" -> "inspection_date"
df.columns = df.columns.str.lower().str.replace(" ", "_")

# 1. Drop never-inspected restaurants (placeholder date, no score or grade)
placeholder = df["inspection_date"] == PLACEHOLDER_DATE
print(
    f"Dropped {placeholder.sum():,} placeholder rows "
    f"({df.loc[placeholder, 'camis'].nunique():,} restaurants)"
)
df = df[~placeholder].copy()

# 2. Types: dates and numbers arrive as text
for col in ["inspection_date", "grade_date", "record_date"]:
    df[col] = pd.to_datetime(df[col], format="%m/%d/%Y")
df["score"] = pd.to_numeric(df["score"]).astype("Int64")  # integer that allows blanks, so no "19.0"
for col in ["latitude", "longitude"]:
    df[col] = pd.to_numeric(df[col])

# 3. Placeholder values that mean "unknown"
df["boro"] = df["boro"].replace("0", pd.NA)
df.loc[df["latitude"] == 0, "latitude"] = pd.NA
df.loc[df["longitude"] == 0, "longitude"] = pd.NA

# 4. Split into three tables
INSPECTION_KEY = ["camis", "inspection_date", "inspection_type"]

restaurants = df[
    ["camis", "dba", "boro", "building", "street", "zipcode",
     "cuisine_description", "nta", "latitude", "longitude"]
].drop_duplicates("camis")

inspection_cols = INSPECTION_KEY + ["score", "grade", "grade_date", "action"]
inspections = df[inspection_cols].drop_duplicates(INSPECTION_KEY)

# Check: score, grade and action should be the same on every row of an inspection
n_versions = df[inspection_cols].drop_duplicates().groupby(INSPECTION_KEY).size()
print(f"Inspections with conflicting score/grade/action: {(n_versions > 1).sum():,}")

violations = df.loc[
    df["violation_code"].notna(),
    INSPECTION_KEY + ["violation_code", "violation_description", "critical_flag"],
]

# 5. Save
OUT_DIR.mkdir(parents=True, exist_ok=True)
for name, table in [("restaurants", restaurants), ("inspections", inspections), ("violations", violations)]:
    table.to_csv(OUT_DIR / f"{name}.csv", index=False)
    print(f"Wrote {OUT_DIR / name}.csv: {len(table):,} rows")
