"""
Q7: do restaurants that miss an A on the first inspection recover at the re-inspection?

Reads data/interim/inspections.csv and pairs each first inspection of a cycle
(Cycle Inspection / Initial Inspection) with the same restaurant's next re-inspection
(Cycle Inspection / Re-inspection), if that comes before the restaurant's next first
inspection. Writes:
    src/data/q7-flow.csv          first-inspection score band x outcome, with counts and shares
    src/data/q7-days.csv          days from the first inspection to the re-inspection, 30-day bins,
                                  for first inspections that scored 14 or more
    src/data/q7-pairs-sample.csv  two matched pairs per outcome, for the sample table on the page
    src/data/q7-summary.json      numbers quoted in the page text

Outcome of a first inspection: a score of 0-13 is an A on the spot. Otherwise the outcome is
the band of the re-inspection score (0-13 A range, 14-27 B range, 28+ C range). A first
inspection from the last 365 days with no re-inspection yet is "awaiting"; an older one is
"no re-inspection on file".
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

IN_FILE = Path("data/interim/inspections.csv")
OUT_DIR = Path("src/data")
FIRST = "Cycle Inspection / Initial Inspection"
REINSPECTION = "Cycle Inspection / Re-inspection"
AWAIT_DAYS = 365  # re-inspections often come months later, so a recent first inspection may still get one
SEED = 6313       # fixed, so the sample rows stay the same between runs

BANDS = ["0-13", "14-27", "28+"]
OUTCOMES = [
    "A at first inspection",
    "Closed at first inspection",
    "A at re-inspection",
    "B range at re-inspection",
    "C range at re-inspection",
    "Re-inspected, no score",
    "Awaiting re-inspection",
    "No re-inspection on file",
    "No first-inspection score",
]
ORDER = {name: i for i, name in enumerate(BANDS + OUTCOMES)}  # display order of the rows
GRADE_CARD = {"A": "A", "B": "B", "C": "C", "Z": "Grade Pending", "P": "Grade Pending",
              "N": "Not Yet Graded"}


def band(score):
    """0-13 earns an A, 14-27 a B, 28 or more a C. A blank score stays blank."""
    labels = np.select([score <= 13, score <= 27], BANDS[:2], default=BANDS[2])
    return pd.Series(labels, index=score.index).where(score.notna())


def share(part, whole):
    return round(float(part) / whole, 6) if whole else None  # 6 places, so the page rounds only once


inspections = pd.read_csv(IN_FILE, dtype={"camis": str}, parse_dates=["inspection_date"])
last_date = inspections["inspection_date"].max()
print(f"Read {len(inspections):,} inspections, the latest on {last_date:%Y-%m-%d}")

# 1. First inspections, each with the date of the same restaurant's next first inspection
first = (
    inspections[inspections["inspection_type"] == FIRST]
    .rename(columns={"inspection_date": "first_date", "score": "first_score"})
    [["camis", "first_date", "first_score", "action"]]
    .sort_values(["camis", "first_date"])
)
first["closed_at_first"] = first["action"].fillna("").str.startswith("Establishment Closed")
first["next_first_date"] = first.groupby("camis")["first_date"].shift(-1)

# 2. Pair each one with the restaurant's next re-inspection...
reinspections = (
    inspections[inspections["inspection_type"] == REINSPECTION]
    .rename(columns={"inspection_date": "reinspection_date", "score": "reinspection_score",
                     "grade": "reinspection_grade"})
    [["camis", "reinspection_date", "reinspection_score", "reinspection_grade"]]
)
pairs = pd.merge_asof(
    first.sort_values("first_date", kind="stable"),
    reinspections.sort_values("reinspection_date", kind="stable"),
    left_on="first_date", right_on="reinspection_date", by="camis",
    direction="forward", allow_exact_matches=False,
)
# ...but only if it comes before the next first inspection (otherwise it belongs to a later cycle)
later_cycle = pairs["reinspection_date"] >= pairs["next_first_date"]
pairs.loc[later_cycle, "reinspection_date"] = pd.NaT
pairs.loc[later_cycle, "reinspection_score"] = np.nan
pairs.loc[later_cycle, "reinspection_grade"] = np.nan
pairs = pairs.sort_values(["camis", "first_date"], kind="stable").reset_index(drop=True)

# 3. What happened after each first inspection
s1, s2 = pairs["first_score"], pairs["reinspection_score"]
recent = (last_date - pairs["first_date"]).dt.days <= AWAIT_DAYS
pairs["first_band"] = band(s1)
pairs["days_to_reinspection"] = (pairs["reinspection_date"] - pairs["first_date"]).dt.days
pairs["outcome"] = np.select(
    [s1.isna(), (s1 <= 13) & pairs["closed_at_first"], s1 <= 13,
     s2 <= 13, s2.between(14, 27), s2 >= 28, pairs["reinspection_date"].notna(), recent],
    ["No first-inspection score", "Closed at first inspection", "A at first inspection",
     "A at re-inspection", "B range at re-inspection", "C range at re-inspection",
     "Re-inspected, no score", "Awaiting re-inspection"],
    default="No re-inspection on file",
)
pairs["grade_after_reinspection"] = pairs["reinspection_grade"].map(GRADE_CARD)

# Check: every first inspection is counted exactly once
assert len(pairs) == len(first), "pairing lost or added first inspections"
print(f"Paired {len(pairs):,} first inspections:")
print(pairs["outcome"].value_counts().to_string())

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 4a. How each first-inspection band splits across outcomes
flow = (
    pairs.dropna(subset=["first_band"])
    .groupby(["first_band", "outcome"]).size()
    .reset_index(name="count")
)
flow["share_of_band"] = (flow["count"] / flow.groupby("first_band")["count"].transform("sum")).round(6)
flow = flow.sort_values(["first_band", "outcome"], key=lambda col: col.map(ORDER))
assert flow["count"].sum() == pairs["first_band"].notna().sum(), "flow counts don't add up"
flow.to_csv(OUT_DIR / "q7-flow.csv", index=False)

# 4b. Days to the re-inspection in 30-day bins (last bin: 360 days or more), for first
# inspections that missed an A. A few first inspections that scored 0-13 also have a
# re-inspection on file; they are counted separately and left out of the waits.
missed = pairs[pairs["first_band"].isin(["14-27", "28+"])]
waited = missed.dropna(subset=["days_to_reinspection"])
n_reinspected_after_a = int(((pairs["first_band"] == "0-13")
                             & pairs["reinspection_date"].notna()).sum())
bin_start = (waited["days_to_reinspection"] // 30 * 30).clip(upper=360).astype(int)
starts = list(range(0, 361, 30))
days = pd.DataFrame({"days": [f"{b}-{b + 29}" if b < 360 else "360+" for b in starts]})
for label, column in [("14-27", "count_14_27"), ("28+", "count_28_plus")]:
    in_band = bin_start[waited["first_band"] == label]
    days[column] = in_band.value_counts().reindex(starts, fill_value=0).to_numpy()
days["count"] = bin_start.value_counts().reindex(starts, fill_value=0).to_numpy()
days["share"] = (days["count"] / max(len(waited), 1)).round(6)
assert (days["count"] == days["count_14_27"] + days["count_28_plus"]).all(), "bins don't add up"
days.to_csv(OUT_DIR / "q7-days.csv", index=False)

# 4c. Two matched pairs per outcome, among first inspections that missed an A
sample =missed.sample(frac=1, random_state=SEED).groupby("outcome").head(2)
sample = sample.sort_values(
    ["outcome", "first_score"],
    key=lambda col: col.map(ORDER) if col.name == "outcome" else col,
)
sample = sample[["camis", "first_date", "first_score", "reinspection_date", "reinspection_score",
                 "grade_after_reinspection", "days_to_reinspection", "outcome"]].copy()
for column in ["first_score", "reinspection_score", "days_to_reinspection"]:
    sample[column] = sample[column].astype("Int64")  # whole numbers, so no "19.0"
sample.to_csv(OUT_DIR / "q7-pairs-sample.csv", index=False)

# 4d. Numbers quoted in the page text
outcome = missed["outcome"]
reinspected = outcome.isin(["A at re-inspection", "B range at re-inspection",
                            "C range at re-inspection"])
waits = waited["days_to_reinspection"]
summary = {
    "last_inspection_date": f"{last_date:%Y-%m-%d}",
    "n_first_inspections": len(pairs),
    "n_missed_a": len(missed),
    "n_a_at_reinspection": int((outcome == "A at re-inspection").sum()),
    "share_a_at_reinspection": share((outcome == "A at re-inspection").sum(), len(missed)),
    "n_awaiting": int((outcome == "Awaiting re-inspection").sum()),
    "share_awaiting": share((outcome == "Awaiting re-inspection").sum(), len(missed)),
    "n_no_reinspection": int((outcome == "No re-inspection on file").sum()),
    "share_recovered_of_reinspected": share((outcome[reinspected] == "A at re-inspection").sum(),
                                            int(reinspected.sum())),
    "median_days_to_reinspection": float(waits.median()) if len(waits) else None,
    "share_reinspected_under_30_days": share((waits < 30).sum(), len(waits)),  # same as the 0-29 bin
    "n_reinspected_after_a": n_reinspected_after_a,
}
(OUT_DIR / "q7-summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
print(f"Wrote q7-flow.csv, q7-days.csv, q7-pairs-sample.csv and q7-summary.json to {OUT_DIR}")
