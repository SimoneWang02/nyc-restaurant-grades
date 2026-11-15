"""
Shared pieces for the question scripts.

Q2 and Q4 use the same grade definition (current_grades below), and Q7 uses the same
card names. Q5 and Q6 use the same inspections: routine initial inspections from 2023
to the end of October 2026, plus the violations cited at them.
"""

from pathlib import Path

import pandas as pd

IN_DIR = Path("data/interim")
OUT_DIR = Path("src/data")
KEY = ["camis", "inspection_date", "inspection_type"]

FIRST_INSPECTION = "Cycle Inspection / Initial Inspection"
START, END = "2023-01-01", "2026-10-29"

# The card a restaurant posts in its window for each grade value.
# Z (grade pending at a hearing) and P (grade pending after reopening) post the same card
GRADE_CARD = {"A": "A", "B": "B", "C": "C",
              "Z": "Grade Pending", "P": "Grade Pending", "N": "Not Yet Graded"}
CARDS = ["A", "B", "C", "Grade Pending", "Not Yet Graded"]


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


def current_grades(inspections):
    """
    One row per restaurant with its current grade: the grade (A, B, C, N, Z or P) of its most
    recent inspection that has one. Restaurants that never had a graded inspection are left out.

    Columns: camis, grade, card, grade_date, latest_letter, latest_letter_date.
    latest_letter is the most recent A, B or C. It is the same as grade unless the current
    grade is N, Z or P, and blank if the restaurant never had a letter.
    """
    graded = inspections[inspections["grade"] != ""].sort_values("inspection_date", kind="stable")

    # Check: no restaurant has two different grades on its latest date, so the row order doesn't matter
    last_date = graded.groupby("camis")["inspection_date"].transform("max")
    on_last = graded[graded["inspection_date"] == last_date]
    assert on_last.groupby("camis")["grade"].nunique().max() == 1, "two grades on the same latest date"

    # N rows have no grade_date, so the date of a grade is the date of its inspection
    current = graded.groupby("camis").tail(1)[["camis", "grade", "inspection_date"]]
    current = current.rename(columns={"inspection_date": "grade_date"}).reset_index(drop=True)
    current["card"] = current["grade"].map(GRADE_CARD)
    assert current["card"].notna().all(), "unknown grade value"

    letters = graded[graded["grade"].isin(["A", "B", "C"])].groupby("camis").tail(1).set_index("camis")
    current["latest_letter"] = current["camis"].map(letters["grade"]).fillna("")
    current["latest_letter_date"] = current["camis"].map(letters["inspection_date"]).fillna("")
    return current[["camis", "grade", "card", "grade_date", "latest_letter", "latest_letter_date"]]


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
