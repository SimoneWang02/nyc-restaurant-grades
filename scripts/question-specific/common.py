"""
Shared pieces for Q4-Q6.

Q5 and Q6 use the same inspections: routine initial inspections from 2023 to the
end of October 2026, plus the violations cited at them.
"""

from pathlib import Path

import pandas as pd

IN_DIR = Path("data/interim")
OUT_DIR = Path("src/data")
KEY = ["camis", "inspection_date", "inspection_type"]

FIRST_INSPECTION = "Cycle Inspection / Initial Inspection"
START, END = "2023-01-01", "2026-10-29"


def read(name):
    # Keep blanks as "" so missing NTA / grade values are easy to test for
    return pd.read_csv(IN_DIR / f"{name}.csv", dtype=str, keep_default_na=False)


def save(table, name):
    # Write booleans as true/false so Observable's typed CSV reads them back as booleans
    table = table.copy()
    for col in table.select_dtypes("bool").columns:
        table[col] = table[col].map({True: "true", False: "false"})
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_DIR / name, index=False)
    print(f"Wrote {OUT_DIR / name}: {len(table):,} rows")


def load_q5_q6():
    restaurants = read("restaurants")
    inspections = read("inspections")
    violations = read("violations")

    # 1. Routine initial inspections in our time window
    first = inspections["inspection_type"] == FIRST_INSPECTION
    in_window = inspections["inspection_date"].between(START, END)
    visits = inspections[first & in_window].copy()
    visits["inspection_id"] = visits[KEY].agg("|".join, axis=1)
    visits = visits.merge(restaurants, on="camis", how="left")
    print(f"{len(visits):,} initial inspections from {START} to {END} "
          f"({(first & ~in_window).sum():,} older ones left out)")

    # 2. Violations cited at those inspections. A few rows are exact copies in the raw file
    cited = violations.merge(visits[KEY + ["inspection_id"]], on=KEY)
    rows = len(cited)
    cited = cited.drop_duplicates()
    assert not cited.duplicated(KEY + ["violation_code"]).any(), "same code cited twice in one inspection"
    print(f"{rows:,} violation rows, {rows - len(cited)} duplicates dropped")

    info = {
        "start": START,
        "end": END,
        "inspections": len(visits),
        "restaurants": int(visits["camis"].nunique()),
        "older_inspections_left_out": int((first & ~in_window).sum()),
        "violation_rows": rows,
        "duplicates_dropped": rows - len(cited),
        "citations": len(cited),
    }
    return visits, cited, info
