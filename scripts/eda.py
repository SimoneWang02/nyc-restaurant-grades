"""
Summarize the raw snapshot and the cleaned tables for the dataset EDA page.

Run from the repo root, after clean.py:  python3 scripts/eda.py

Writes src/data/eda.json (small, committed), which src/dataset-eda.md reads.
The raw CSV and data/interim/ are not in git, so the page cannot read them directly.
"""

import json
from pathlib import Path

import pandas as pd

IN_DIR = Path("data/interim")
OUT = Path("src/data/eda.json")
PLACEHOLDER_DATE = "01/01/1900"


def records(table):
    """DataFrame -> list of dicts, with blanks as null."""
    return json.loads(table.to_json(orient="records"))


def counts(series):
    """Value counts including blanks, as [{value, n, share}]."""
    vc = series.fillna("(blank)").value_counts()
    return [{"value": v, "n": int(n), "share": n / len(series)} for v, n in vc.items()]


def missing(table):
    """Blank cells per column, as [{column, missing, share}]."""
    na = table.isna().sum()
    return [{"column": c, "missing": int(n), "share": n / len(table)} for c, n in na.items()]


raw_path = sorted(Path("data/raw").glob("inspections_*.csv"))[-1]
raw = pd.read_csv(raw_path, dtype=str)
placeholder = raw["INSPECTION DATE"] == PLACEHOLDER_DATE

# Read as text so dates stay as "YYYY-MM-DD" in the JSON
restaurants = pd.read_csv(IN_DIR / "restaurants.csv", dtype=str)
inspections = pd.read_csv(IN_DIR / "inspections.csv", dtype=str)
violations = pd.read_csv(IN_DIR / "violations.csv", dtype=str)

# One restaurant traced through the split: first (by CAMIS) with exactly two
# inspections, one of them a first inspection over 13 points
key = ["camis", "inspection_date", "inspection_type"]
two = inspections.groupby("camis").filter(lambda g: len(g) == 2)
failed_first = two[
    (two["inspection_type"] == "Cycle Inspection / Initial Inspection")
    & (pd.to_numeric(two["score"]) > 13)
]
example = sorted(failed_first["camis"])[0]
example_raw = raw[raw["CAMIS"] == example].sort_values("INSPECTION DATE")

years = inspections["inspection_date"].str[:4].value_counts().sort_index()

eda = {
    "snapshot": raw_path.name,
    "raw": {
        "rows": len(raw),
        "columns": len(raw.columns),
        "restaurants": int(raw["CAMIS"].nunique()),
        "placeholder_rows": int(placeholder.sum()),
        "placeholder_restaurants": int(raw.loc[placeholder, "CAMIS"].nunique()),
        "head": records(raw.head(5)),
    },
    "tables": {
        name: {"rows": len(t), "head": records(t.head(5)), "missing": missing(t)}
        for name, t in [("restaurants", restaurants), ("inspections", inspections), ("violations", violations)]
    },
    "example": {
        "camis": example,
        "raw": records(example_raw[["INSPECTION DATE", "INSPECTION TYPE", "VIOLATION CODE", "SCORE", "GRADE", "ACTION"]]),
        "inspections": records(inspections[inspections["camis"] == example]),
        "violations": records(violations[violations["camis"] == example][key + ["violation_code", "critical_flag"]]),
    },
    "counts": {
        "inspection_type": counts(inspections["inspection_type"]),
        "grade": counts(inspections["grade"]),
        "action": counts(inspections["action"]),
        "boro": counts(restaurants["boro"]),
        "critical_flag": counts(violations["critical_flag"]),
    },
    "dates": {
        "min": inspections["inspection_date"].min(),
        "max": inspections["inspection_date"].max(),
        "per_year": [{"year": y, "inspections": int(n)} for y, n in years.items()],
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(eda, indent=1))
print(f"Wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} KB), example restaurant {example}")
