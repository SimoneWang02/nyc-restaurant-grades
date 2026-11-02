"""
Q1: how are first-inspection scores distributed?

Reads data/interim/inspections.csv and writes src/data/q1-scores.csv where each row is the count of inspections per score
"""

from pathlib import Path

import pandas as pd

IN_FILE = Path("data/interim/inspections.csv")
OUT_FILE = Path("src/data/q1-scores.csv")
FIRST_INSPECTION = "Cycle Inspection / Initial Inspection"

inspections = pd.read_csv(IN_FILE, dtype={"camis": str})
print(f"Read {len(inspections):,} inspections")

# 1. Keep only first inspections
first = inspections[inspections["inspection_type"] == FIRST_INSPECTION].copy()
first = first.dropna(subset=["score"])
first["score"] = first["score"].astype(int)

# 2. Count inspections per score
counts = first.groupby('score').size()

# 3. Fill in scores nobody got so the chart shows the gaps as empty bars
scores = (
    counts.reindex(range(0, counts.index.max() + 1), fill_value=0)
        .rename_axis("score")
        .reset_index(name="count")
)

# 4. Save
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
scores.to_csv(OUT_FILE, index=False)
print(f"Wrote {OUT_FILE}: {len(scores):,} rows, {scores['count'].sum():,} inspections")