"""
Q8: which restaurants get closed, and how long does it take them to reopen?

Reads data/interim/inspections.csv, violations.csv and restaurants.csv and follows each
closure to the reopening that ends it. Writes:
    src/data/q8-matching.csv     how closures end (reopened, or what is on file instead)
    src/data/q8-jan2025.csv      every closure that began January 1-10, 2025: the small sample
                                 we checked first (M1 feedback, point 2)
    src/data/q8-violations.csv   the 15 violations cited most at closures, with how often each
                                 one is cited at first inspections, for comparison
    src/data/q8-days-closed.csv  days closed, for closures that reopened
    src/data/q8-summary.json     numbers quoted in the page text

A closure starts at an inspection whose action begins "Establishment Closed" and ends at the
same restaurant's next "Establishment re-opened" record. "Re-closed" records in between, and
reopening inspections that close the restaurant again, count as failed reopening attempts.
A closure with no reopening on file is labeled by what comes after it.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

IN_DIR = Path("data/interim")
OUT_DIR = Path("src/data")
KEY = ["camis", "inspection_date", "inspection_type"]
FIRST = "Cycle Inspection / Initial Inspection"
REOPENING = "Reopening Inspection"
GRADED_PROGRAMS = ["Cycle Inspection", "Pre-permit (Operational)"]  # programs that give letter grades
STAGE_ORDER = {"Initial Inspection": 0, "Re-inspection": 1, "Compliance Inspection": 2,
               "Second Compliance Inspection": 3, "Reopening Inspection": 4}  # same-day order
RECENT_DAYS = 30  # a closure this recent may simply not have reopened yet
STATUSES = [
    "Reopened",
    "No reopening record (closed over 30 days before the data pull)",
    "Closed again before a reopening record",
    "Still closed at the data pull (closed in the last 30 days)",
    "Inspected again without a reopening record",
]
DAY_BINS = [-1, 0, 1, 3, 7, 14, 30, 90, np.inf]
DAY_LABELS = ["0 (same day)", "1", "2-3", "4-7", "8-14", "15-30", "31-90", "91+"]


def share(part, whole):
    return round(float(part) / whole, 6) if whole else None  # 6 places, so the page rounds only once


def most_common(values):
    return values.mode().iat[0]


inspections = pd.read_csv(IN_DIR / "inspections.csv", dtype={"camis": str},
                          parse_dates=["inspection_date"])
violations = pd.read_csv(IN_DIR / "violations.csv", dtype={"camis": str},
                         parse_dates=["inspection_date"])
restaurants = pd.read_csv(IN_DIR / "restaurants.csv", dtype={"camis": str})
last_date = inspections["inspection_date"].max()
print(f"Read {len(inspections):,} inspections, the latest on {last_date:%Y-%m-%d}")

# 1. Split "Cycle Inspection / Re-inspection" into program and stage, and flag closure records
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
    return {"camis": camis, "closed_on": row.inspection_date,
            "closing_inspection": row.inspection_type, "failed_reopenings": 0,
            "reopened_on": pd.NaT, "status": None}


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

episodes = pd.DataFrame(episodes, columns=["camis", "closed_on", "closing_inspection",
                                           "failed_reopenings", "reopened_on", "status"])
for column in ["closed_on", "reopened_on"]:
    episodes[column] = pd.to_datetime(episodes[column])
episodes["days_closed"] = (episodes["reopened_on"] - episodes["closed_on"]).dt.days.astype("Int64")
episodes = episodes.merge(restaurants[["camis", "dba", "boro"]], on="camis", how="left",
                          validate="many_to_one")
print(f"{len(episodes):,} closures at {episodes['camis'].nunique():,} restaurants:")
print(episodes["status"].value_counts().to_string())
print(f"Records with no closure on file: {orphans}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 3a. How closures end
matching = (
    episodes.groupby("status")
    .agg(closures=("camis", "size"), restaurants=("camis", "nunique"))
    .reindex(STATUSES).dropna().astype(int).reset_index()
)
matching["share"] = (matching["closures"] / max(len(episodes), 1)).round(6)
assert matching["closures"].sum() == len(episodes), "every closure needs exactly one status"
matching.to_csv(OUT_DIR / "q8-matching.csv", index=False)

# 3b. The small sample we checked first: closures that began January 1-10, 2025
jan = episodes[episodes["closed_on"].between("2025-01-01", "2025-01-10")].sort_values(
    ["closed_on", "camis"], kind="stable")
jan[["camis", "dba", "closed_on", "closing_inspection", "failed_reopenings", "reopened_on",
     "days_closed", "status"]].to_csv(OUT_DIR / "q8-jan2025.csv", index=False)

# 3c. Violations cited at the inspection that closed the restaurant, against first inspections
closings = inspections.loc[inspections["closed"] & (inspections["stage"] != REOPENING), KEY]
firsts = inspections.loc[inspections["inspection_type"] == FIRST, KEY]
at_closing = violations.merge(closings, on=KEY).drop_duplicates(KEY + ["violation_code"])
at_first = violations.merge(firsts, on=KEY).drop_duplicates(KEY + ["violation_code"])
top = at_closing.groupby("violation_code").agg(
    violation_description=("violation_description", most_common),
    critical_flag=("critical_flag", most_common),
    closures_citing=("camis", "size"),
)
top["share_of_closures"] = (top["closures_citing"] / max(len(closings), 1)).round(6)
top["share_of_first_inspections"] = (at_first.groupby("violation_code").size()
                                     / max(len(firsts), 1)).round(6)
top = top.sort_values("closures_citing", ascending=False, kind="stable").head(15).reset_index()
top.to_csv(OUT_DIR / "q8-violations.csv", index=False)

# 3d. Days closed, for closures that reopened, split by whether a reopening attempt failed first
reopened = episodes[episodes["status"] == "Reopened"].copy()
assert (reopened["days_closed"] >= 0).all(), "a reopening before its closure"
reopened["bin"] = pd.cut(reopened["days_closed"].astype(float), bins=DAY_BINS, labels=DAY_LABELS)
failed_first = reopened["failed_reopenings"] > 0
days_closed = pd.DataFrame({"days_closed": DAY_LABELS})
days_closed["reopened_first_try"] = (reopened.loc[~failed_first, "bin"].value_counts()
                                     .reindex(DAY_LABELS, fill_value=0).to_numpy())
days_closed["reopened_after_failed_try"] = (reopened.loc[failed_first, "bin"].value_counts()
                                            .reindex(DAY_LABELS, fill_value=0).to_numpy())
days_closed["count"] = days_closed["reopened_first_try"] + days_closed["reopened_after_failed_try"]
days_closed.to_csv(OUT_DIR / "q8-days-closed.csv", index=False)

# 3e. Numbers quoted in the page text
waits = reopened["days_closed"].astype(float)
leader = top.iloc[0] if len(top) else None
summary = {
    "last_inspection_date": f"{last_date:%Y-%m-%d}",
    "n_closures": len(episodes),
    "n_restaurants": int(episodes["camis"].nunique()),
    "n_reopened": len(reopened),
    "share_reopened": share(len(reopened), len(episodes)),
    "median_days_closed": float(waits.median()) if len(waits) else None,
    "p25_days_closed": float(waits.quantile(0.25)) if len(waits) else None,
    "p75_days_closed": float(waits.quantile(0.75)) if len(waits) else None,
    "share_with_failed_reopening": share((episodes["failed_reopenings"] > 0).sum(), len(episodes)),
    "top_code": None if leader is None else str(leader["violation_code"]),
    "top_code_description": (None if leader is None
                             else str(leader["violation_description"]).strip().rstrip(".")),
    "top_code_share": None if leader is None else float(leader["share_of_closures"]),
    "top_code_first_share": (None if leader is None or pd.isna(leader["share_of_first_inspections"])
                             else float(leader["share_of_first_inspections"])),
    "n_jan_sample": len(jan),
    "n_jan_sample_reopened": int((jan["status"] == "Reopened").sum()),
    **orphans,
}
(OUT_DIR / "q8-summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
print(f"Wrote q8-matching.csv, q8-jan2025.csv, q8-violations.csv, q8-days-closed.csv and "
      f"q8-summary.json to {OUT_DIR}")
