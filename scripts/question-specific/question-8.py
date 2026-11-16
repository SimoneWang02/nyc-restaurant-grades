"""
Q8: which restaurants get closed, and how long does it take them to reopen?

A closure starts at an inspection whose action begins "Establishment Closed" and ends at the
same restaurant's next "Establishment re-opened" record. "Re-closed" records in between, and
reopening inspections that close the restaurant again, count as failed reopening attempts.
A closure with no reopening on file is labeled by the rule that applies to what comes after it.
Closures are followed through the whole file; those that began from START to END are kept.
Writes q8-matching.csv, q8-jan2025.csv, q8-violations.csv, q8-days-closed.csv and
q8-summary.json to src/data/.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import END, START, snapshot

IN_DIR = Path("data/interim")
OUT_DIR = Path("src/data")
KEY = ["camis", "inspection_date", "inspection_type"]
FIRST = "Cycle Inspection / Initial Inspection"
REOPENING = "Reopening Inspection"
GRADED_PROGRAMS = ["Cycle Inspection", "Pre-permit (Operational)"]
STAGE_ORDER = {"Initial Inspection": 0, "Re-inspection": 1, "Compliance Inspection": 2,
               "Second Compliance Inspection": 3, "Reopening Inspection": 4}  # same-day order
RECENT_DAYS = 30
STATUSES = [
    "Reopened",
    "No reopening on file (closed over 30 days before the end of follow-up)",
    "Closed again before a reopening record",
    "Recent closure, no reopening on file (last 30 days)",
    "Inspected again without a reopening record",
]
DAY_BINS = [-1, 0, 1, 3, 7, 14, 30, 90, np.inf]
DAY_LABELS = ["0 (same day)", "1", "2-3", "4-7", "8-14", "15-30", "31-90", "91+"]


def share(part, whole):
    return round(float(part) / whole, 6) if whole else None  # 6 places, so the page rounds only once


try:
    SNAPSHOT = snapshot()
except IndexError:  # no data/raw/inspections_*.csv on this computer
    SNAPSHOT = None

inspections = pd.read_csv(IN_DIR / "inspections.csv", dtype={"camis": str}, parse_dates=["inspection_date"])
violations = pd.read_csv(IN_DIR / "violations.csv", dtype={"camis": str}, parse_dates=["inspection_date"])
restaurants = pd.read_csv(IN_DIR / "restaurants.csv", dtype={"camis": str})
last_date = inspections["inspection_date"].max()  # end of follow-up
print(f"Read {len(inspections):,} inspections, the latest on {last_date:%Y-%m-%d}")

# 1. Program and stage of each inspection, and the closure-related actions
parts = inspections["inspection_type"].str.split(" / ", n=1, expand=True).reindex(columns=[0, 1])
inspections["program"] = parts[0].str.strip()
inspections["stage"] = parts[1].str.strip()
inspections["stage_order"] = inspections["stage"].map(STAGE_ORDER).fillna(9)
action = inspections["action"].fillna("")
inspections["closed"] = action.str.startswith("Establishment Closed")
inspections["reclosed"] = action.str.contains("re-closed", case=False, regex=False)
inspections["reopened"] = action.str.contains("re-opened", case=False, regex=False)

# 2. Walk through each closed restaurant's inspections in date order
flagged = inspections["closed"] | inspections["reclosed"] | inspections["reopened"]
history = (inspections[inspections["camis"].isin(inspections.loc[flagged, "camis"])]
           .sort_values(["camis", "inspection_date", "stage_order"], kind="stable"))
episodes = []
orphans = {"reopened_without_closure": 0, "reclosed_without_closure": 0}


def new_episode(camis, row):
    return {"camis": camis, "closed_on": row.inspection_date, "closing_inspection": row.inspection_type,
            "failed_reopenings": 0, "reopened_on": pd.NaT, "status": None}


for camis, rows in history.groupby("camis", sort=False):
    episode = None
    for row in rows.itertuples(index=False):
        if row.closed:
            if episode is None:
                episode = new_episode(camis, row)
            elif row.stage == REOPENING:
                episode["failed_reopenings"] += 1  # a reopening inspection that closed it again
            else:
                episode["status"] = "Closed again before a reopening record"
                episodes.append(episode)
                episode = new_episode(camis, row)
        elif row.reclosed:
            if episode is None:
                orphans["reclosed_without_closure"] += 1
            else:
                episode["failed_reopenings"] += 1
        elif row.reopened:
            if episode is None:
                orphans["reopened_without_closure"] += 1
            else:
                episode["reopened_on"], episode["status"] = row.inspection_date, "Reopened"
                episodes.append(episode)
                episode = None
        elif (episode is not None and row.program in GRADED_PROGRAMS and row.stage != REOPENING
              and row.inspection_date > episode["closed_on"]):
            episode["status"] = "Inspected again without a reopening record"
            episodes.append(episode)
            episode = None
    if episode is not None:  # still open at the end of the file
        recent = (last_date - episode["closed_on"]).days <= RECENT_DAYS
        episode["status"] = STATUSES[3] if recent else STATUSES[1]
        episodes.append(episode)

episodes = pd.DataFrame(episodes)
episodes["reopened_on"] = pd.to_datetime(episodes["reopened_on"])
episodes["days_closed"] = (episodes["reopened_on"] - episodes["closed_on"]).dt.days.astype("Int64")
episodes = episodes.merge(restaurants[["camis", "dba", "boro"]], on="camis", how="left", validate="many_to_one")
n_closures_before_window = int((episodes["closed_on"] < START).sum())
episodes = episodes[episodes["closed_on"].between(START, END)].reset_index(drop=True)
print(episodes["status"].value_counts().to_string())

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 3a. How closures end
matching = (episodes.groupby("status").agg(closures=("camis", "size"), restaurants=("camis", "nunique"))
            .reindex(STATUSES).dropna().astype(int).reset_index())
matching["share"] = (matching["closures"] / len(episodes)).round(6)
assert matching["closures"].sum() == len(episodes), "every closure needs exactly one status"
matching.to_csv(OUT_DIR / "q8-matching.csv", index=False)

# 3b. The sample we checked first: closures that began January 1-10, 2025
jan = episodes[episodes["closed_on"].between("2025-01-01", "2025-01-10")].sort_values(["closed_on", "camis"], kind="stable")
jan[["camis", "dba", "closed_on", "closing_inspection", "failed_reopenings", "reopened_on",
     "days_closed", "status"]].to_csv(OUT_DIR / "q8-jan2025.csv", index=False)

# 3c. Violations cited at closing inspections, against first inspections in the same window
in_window = inspections["inspection_date"].between(START, END)
closings = inspections.loc[inspections["closed"] & (inspections["stage"] != REOPENING) & in_window, KEY]
firsts = inspections.loc[(inspections["inspection_type"] == FIRST) & in_window, KEY]
at_closing = violations.merge(closings, on=KEY).drop_duplicates(KEY + ["violation_code"])
at_first = violations.merge(firsts, on=KEY).drop_duplicates(KEY + ["violation_code"])
top = at_closing.groupby("violation_code").agg(
    violation_description=("violation_description", lambda v: v.mode().iat[0]),
    critical_flag=("critical_flag", lambda v: v.mode().iat[0]),
    closures_citing=("camis", "size"),
)
top["share_of_closures"] = (top["closures_citing"] / len(closings)).round(6)
top["share_of_first_inspections"] = (at_first.groupby("violation_code").size() / len(firsts)).round(6)
top = top.sort_values("closures_citing", ascending=False, kind="stable").head(15).reset_index()
top.to_csv(OUT_DIR / "q8-violations.csv", index=False)

# 3d. Days closed, for closures that reopened, split by whether a reopening attempt failed first
reopened = episodes[episodes["status"] == "Reopened"].copy()
reopened["bin"] = pd.cut(reopened["days_closed"].astype(float), bins=DAY_BINS, labels=DAY_LABELS)
failed_first = reopened["failed_reopenings"] > 0
days_closed = pd.DataFrame({"days_closed": DAY_LABELS})
days_closed["reopened_first_try"] = reopened.loc[~failed_first, "bin"].value_counts().reindex(DAY_LABELS, fill_value=0).to_numpy()
days_closed["reopened_after_failed_try"] = reopened.loc[failed_first, "bin"].value_counts().reindex(DAY_LABELS, fill_value=0).to_numpy()
days_closed["count"] = days_closed["reopened_first_try"] + days_closed["reopened_after_failed_try"]
days_closed.to_csv(OUT_DIR / "q8-days-closed.csv", index=False)

# 3e. Numbers quoted on the page
waits = reopened["days_closed"].astype(float)
leader = top.iloc[0]
summary = {
    "snapshot": SNAPSHOT,
    "window_start": START,
    "window_end": END,
    "last_inspection_date": f"{last_date:%Y-%m-%d}",
    "n_closures_before_window": n_closures_before_window,
    "n_closures": len(episodes),
    "n_restaurants": int(episodes["camis"].nunique()),
    "n_reopened": len(reopened),
    "share_reopened": share(len(reopened), len(episodes)),
    "median_days_closed": float(waits.median()),
    "p25_days_closed": float(waits.quantile(0.25)),
    "p75_days_closed": float(waits.quantile(0.75)),
    "share_with_failed_reopening": share((episodes["failed_reopenings"] > 0).sum(), len(episodes)),
    "n_closing_inspections": len(closings),
    "n_reopened_first_try": int((~failed_first).sum()),
    "n_reopened_after_failed_try": int(failed_first.sum()),
    "median_days_first_try": float(waits[~failed_first].median()),
    "median_days_after_failed_try": float(waits[failed_first].median()),
    "top_code": str(leader["violation_code"]),
    "top_code_description": str(leader["violation_description"]).strip().rstrip("."),
    "top_code_share": float(leader["share_of_closures"]),
    "top_code_first_share": float(leader["share_of_first_inspections"]),
    "n_jan_sample": len(jan),
    "n_jan_sample_reopened": int((jan["status"] == "Reopened").sum()),
    **orphans,
}
(OUT_DIR / "q8-summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
