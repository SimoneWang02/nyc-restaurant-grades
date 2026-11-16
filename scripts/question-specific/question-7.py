"""
Q7: do restaurants that miss an A on the first inspection recover at the re-inspection?

Pairs each first inspection (Cycle Inspection / Initial Inspection) from START to END with the
same restaurant's next Cycle Inspection / Re-inspection, if that comes before the restaurant's
next first inspection. Writes q7-flow.csv, q7-days.csv, q7-pairs-sample.csv and
q7-summary.json to src/data/.

With no re-inspection on file, the label names the rule that applies: the next first inspection
came first; or the first inspection is within 365 days of the end of follow-up (the latest
inspection date in the file); or it is older than that.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import END, GRADE_CARD, START, snapshot

IN_FILE = Path("data/interim/inspections.csv")
OUT_DIR = Path("src/data")
FIRST = "Cycle Inspection / Initial Inspection"
REINSPECTION = "Cycle Inspection / Re-inspection"
FOLLOW_UP_DAYS = 365
LONG_WAIT_DAYS = 180
SEED = 6313  # fixed, so the sample rows stay the same between runs

NEXT_CYCLE = "Next cycle began, no re-inspection on file"
RECENT = "No re-inspection on file, first inspection within 365 days of the end of follow-up"
OLDER = "No re-inspection on file, first inspection more than 365 days before the end of follow-up"
BANDS = ["0-13", "14-27", "28+"]
OUTCOMES = ["A at first inspection", "Closed at first inspection", "A at re-inspection",
            "B range at re-inspection", "C range at re-inspection", "Re-inspected, no score",
            NEXT_CYCLE, RECENT, OLDER, "No first-inspection score"]
ORDER = {name: i for i, name in enumerate(BANDS + OUTCOMES)}


def band(score):
    labels = np.select([score <= 13, score <= 27], BANDS[:2], default=BANDS[2])
    return pd.Series(labels, index=score.index).where(score.notna())


def share(part, whole):
    return round(float(part) / whole, 6) if whole else None  # 6 places, so the page rounds only once


def median(values):
    return float(values.median()) if len(values) else None


try:
    SNAPSHOT = snapshot()
except IndexError:  # no data/raw/inspections_*.csv on this computer
    SNAPSHOT = None

inspections = pd.read_csv(IN_FILE, dtype={"camis": str}, parse_dates=["inspection_date"])
last_date = inspections["inspection_date"].max()  # end of follow-up
print(f"Read {len(inspections):,} inspections, the latest on {last_date:%Y-%m-%d}")

# 1. First inspections. The next first inspection is found before the window is applied.
first = (
    inspections[inspections["inspection_type"] == FIRST]
    .rename(columns={"inspection_date": "first_date", "score": "first_score"})
    [["camis", "first_date", "first_score", "action"]]
    .sort_values(["camis", "first_date"])
)
first["closed_at_first"] = first["action"].fillna("").str.startswith("Establishment Closed")
first["next_first_date"] = first.groupby("camis")["first_date"].shift(-1)
n_before_window = int((first["first_date"] < START).sum())
first = first[first["first_date"].between(START, END)]

# 2. Pair each one with the next re-inspection, unless it belongs to a later cycle
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
later_cycle = pairs["reinspection_date"] >= pairs["next_first_date"]
pairs.loc[later_cycle, ["reinspection_date", "reinspection_score", "reinspection_grade"]] = np.nan
pairs = pairs.sort_values(["camis", "first_date"], kind="stable").reset_index(drop=True)

# Re-inspections in the window that no first inspection claims
paired = pairs.dropna(subset=["reinspection_date"])[["camis", "reinspection_date"]].drop_duplicates()
in_window = reinspections[reinspections["reinspection_date"].between(START, END)]
unpaired = in_window.merge(paired, how="left", indicator=True)["_merge"] == "left_only"

# 3. Outcome of each first inspection. A later first inspection ends the cycle whatever its date.
s1, s2 = pairs["first_score"], pairs["reinspection_score"]
recent = (last_date - pairs["first_date"]).dt.days <= FOLLOW_UP_DAYS
pairs["first_band"] = band(s1)
pairs["days_to_reinspection"] = (pairs["reinspection_date"] - pairs["first_date"]).dt.days
pairs["outcome"] = np.select(
    [s1.isna(), (s1 <= 13) & pairs["closed_at_first"], s1 <= 13,
     s2 <= 13, s2.between(14, 27), s2 >= 28, pairs["reinspection_date"].notna(),
     pairs["next_first_date"].notna(), recent],
    ["No first-inspection score", "Closed at first inspection", "A at first inspection",
     "A at re-inspection", "B range at re-inspection", "C range at re-inspection",
     "Re-inspected, no score", NEXT_CYCLE, RECENT],
    default=OLDER,
)
pairs["grade_after_reinspection"] = pairs["reinspection_grade"].map(GRADE_CARD)
assert len(pairs) == len(first), "pairing lost or added first inspections"
print(pairs["outcome"].value_counts().to_string())

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 4a. Band x outcome
flow = pairs.dropna(subset=["first_band"]).groupby(["first_band", "outcome"]).size().reset_index(name="count")
flow["share_of_band"] = (flow["count"] / flow.groupby("first_band")["count"].transform("sum")).round(6)
flow = flow.sort_values(["first_band", "outcome"], key=lambda col: col.map(ORDER))
flow.to_csv(OUT_DIR / "q7-flow.csv", index=False)

# 4b. Days to the re-inspection in 30-day bins (last bin 360+), for first scores of 14 or more
missed = pairs[pairs["first_band"].isin(["14-27", "28+"])]
waited = missed.dropna(subset=["days_to_reinspection"]).copy()
bin_start = (waited["days_to_reinspection"] // 30 * 30).clip(upper=360).astype(int)
starts = list(range(0, 361, 30))
days = pd.DataFrame({"days": [f"{b}-{b + 29}" if b < 360 else "360+" for b in starts]})
for label, column in [("14-27", "count_14_27"), ("28+", "count_28_plus")]:
    days[column] = bin_start[waited["first_band"] == label].value_counts().reindex(starts, fill_value=0).to_numpy()
days["count"] = days["count_14_27"] + days["count_28_plus"]
days["share"] = (days["count"] / max(len(waited), 1)).round(6)
days.to_csv(OUT_DIR / "q7-days.csv", index=False)

# 4c. Long waits: was the restaurant closed at some point between the two inspections?
closures = inspections.loc[inspections["action"].fillna("").str.startswith("Establishment Closed"),
                           ["camis", "inspection_date"]]
in_cycle = waited.reset_index()[["index", "camis", "first_date", "reinspection_date"]].merge(closures, on="camis")
in_cycle = in_cycle[(in_cycle["inspection_date"] >= in_cycle["first_date"])
                    & (in_cycle["inspection_date"] < in_cycle["reinspection_date"])]
waited["closure_in_cycle"] = waited.index.isin(in_cycle["index"])
long_wait = waited["days_to_reinspection"] > LONG_WAIT_DAYS
followed_a_year = (last_date - waited["first_date"]).dt.days >= FOLLOW_UP_DAYS  # less affected by the cutoff

# 4d. Two matched pairs per outcome
sample = missed.sample(frac=1, random_state=SEED).groupby("outcome").head(2)
sample = sample.sort_values(["outcome", "first_score"],
                            key=lambda col: col.map(ORDER) if col.name == "outcome" else col)
sample = sample[["camis", "first_date", "first_score", "reinspection_date", "reinspection_score",
                 "grade_after_reinspection", "days_to_reinspection", "outcome"]].copy()
for column in ["first_score", "reinspection_score", "days_to_reinspection"]:
    sample[column] = sample[column].astype("Int64")
sample.to_csv(OUT_DIR / "q7-pairs-sample.csv", index=False)

# 4e. Numbers quoted on the page
outcome = missed["outcome"]
scored = outcome.isin(["A at re-inspection", "B range at re-inspection", "C range at re-inspection"])
waits = waited["days_to_reinspection"]
summary = {
    "snapshot": SNAPSHOT,
    "window_start": START,
    "window_end": END,
    "last_inspection_date": f"{last_date:%Y-%m-%d}",
    "follow_up_days": FOLLOW_UP_DAYS,
    "n_first_inspections": len(pairs),
    "n_first_inspections_before_window": n_before_window,
    "n_missed_a": len(missed),
    "n_a_at_reinspection": int((outcome == "A at re-inspection").sum()),
    "share_a_at_reinspection": share((outcome == "A at re-inspection").sum(), len(missed)),
    "n_scored_reinspections": int(scored.sum()),
    "share_recovered_of_reinspected": share((outcome[scored] == "A at re-inspection").sum(), scored.sum()),
    "n_next_cycle_no_reinspection": int((outcome == NEXT_CYCLE).sum()),
    "n_recent_no_reinspection": int((outcome == RECENT).sum()),
    "share_recent_no_reinspection": share((outcome == RECENT).sum(), len(missed)),
    "n_older_no_reinspection": int((outcome == OLDER).sum()),
    "n_reinspected_no_score": int((outcome == "Re-inspected, no score").sum()),
    "n_reinspected_after_a": int(((pairs["first_band"] == "0-13") & pairs["reinspection_date"].notna()).sum()),
    "n_moved_to_later_cycle": int(later_cycle.sum()),
    "n_reinspections_in_window": len(in_window),
    "n_unpaired_reinspections": int(unpaired.sum()),
    "median_days_to_reinspection": median(waits),
    "median_days_14_27": median(waits[waited["first_band"] == "14-27"]),
    "median_days_28_plus": median(waits[waited["first_band"] == "28+"]),
    "share_reinspected_under_30_days": share((waits < 30).sum(), len(waits)),
    "median_days_followed_a_year": median(waits[followed_a_year]),
    "long_wait_days": LONG_WAIT_DAYS,
    "n_long_waits": int(long_wait.sum()),
    "share_long_waits": share(long_wait.sum(), len(waits)),
    "share_long_waits_with_closure": share((long_wait & waited["closure_in_cycle"]).sum(), long_wait.sum()),
    "n_waits_with_closure": int(waited["closure_in_cycle"].sum()),
    "median_days_with_closure": median(waits[waited["closure_in_cycle"]]),
    "median_days_without_closure": median(waits[~waited["closure_in_cycle"]]),
}
(OUT_DIR / "q7-summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
