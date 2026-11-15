"""
Q1: how are first-inspection scores distributed?

Reads data/interim/inspections.csv, keeps the routine first inspections in the shared time
window (START to END in common.py, the same as Q5 and Q6) and writes:
    src/data/q1-scores.csv      number of first inspections per score, one row per score
    src/data/q1-summary.json    window, snapshot and the counts quoted in the page text
Run from the repo root: python3 scripts/question-specific/question-1.py
"""

import json

from common import END, FIRST_INSPECTION, OUT_DIR, START, read, save, snapshot

inspections = read("inspections")
print(f"Read {len(inspections):,} inspections")

# 1. Keep only first inspections in the time window. The file keeps about three years,
# so the few older ones are leftovers, not a fair sample of their years
first = inspections[inspections["inspection_type"] == FIRST_INSPECTION]
in_window = first["inspection_date"].between(START, END)
no_score = first["score"] == ""
print(f"{(~in_window).sum():,} first inspections before {START} left out, "
      f"{(in_window & no_score).sum():,} without a score left out")
first = first[in_window & ~no_score].copy()
first["score"] = first["score"].astype(float).astype(int)

# 2. Count inspections per score
counts = first.groupby("score").size()

# 3. Fill in scores nobody got so the chart shows the gaps as empty bars
scores = (
    counts.reindex(range(0, counts.index.max() + 1), fill_value=0)
        .rename_axis("score")
        .reset_index(name="count")
)
assert scores["count"].sum() == len(first), "score counts don't add up"

# 4. Save the counts, and the numbers the page quotes
save(scores, "q1-scores.csv")
count_at = scores.set_index("score")["count"]
summary = {
    "snapshot": snapshot(),
    "start": START,
    "end": END,
    "inspections": len(first),
    "older_left_out": int((~in_window).sum()),
    "no_score_left_out": int((in_window & no_score).sum()),
    "count_12": int(count_at.get(12, 0)),
    "count_13": int(count_at.get(13, 0)),
    "count_14": int(count_at.get(14, 0)),
    "share_a_range": round(float(count_at.loc[:13].sum()) / len(first), 6),
    "max_score": int(scores["score"].max()),
}
(OUT_DIR / "q1-summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
