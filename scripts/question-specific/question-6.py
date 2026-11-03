"""
Q6: where do mice, cockroaches and flies show up most, by neighborhood and by cuisine?

Run from the repo root: python3 scripts/question-specific/question-6.py
Needs data/reference/nta-2010.csv (python3 scripts/download-nta-lookup.py).
Writes src/data/q6-*.csv and q6-summary.json
"""

import json

import pandas as pd

from common import OUT_DIR, load_q5_q6, save

# 04N is "flies or other nuisance pests". Rats (04K) are left out on purpose
PESTS = {"04L": "mice", "04M": "roaches", "04N": "flies"}
LABELS = {"mice": "Mice or evidence of mice", "roaches": "Cockroaches",
          "flies": "Flies or other nuisance pests", "any_pest": "Any of the three"}
MIN_INSPECTIONS = 30  # smaller groups stay in the tables but are not compared

visits, cited, info = load_q5_q6()

# 1. One row per inspection with a yes/no for each pest code.
# Inspections with no violation at all stay in, they count as "no pest"
for code, name in PESTS.items():
    visits[name] = visits["inspection_id"].isin(cited.loc[cited["violation_code"] == code, "inspection_id"])
visits["any_pest"] = visits[list(PESTS.values())].any(axis=1)  # mice + roaches in one visit counts once

# 2. NTA names (the inspection data only has codes like "MN17")
names = pd.read_csv("data/reference/nta-2010.csv", dtype=str)
visits = visits.merge(names, on="nta", how="left")
visits.loc[visits["nta"] == "", "nta_name"] = "Missing NTA"
assert visits["nta_name"].notna().all(), "an NTA code has no name in the lookup"
visits["cuisine"] = visits["cuisine_description"].replace("", "Unknown")


# 3. Share of inspections with each pest, per group
def rates(groups):
    table = visits.groupby(groups).agg(
        inspections=("inspection_id", "size"),
        restaurants=("camis", "nunique"),
        mice=("mice", "sum"),
        roaches=("roaches", "sum"),
        flies=("flies", "sum"),
        any_pest=("any_pest", "sum"),
    ).reset_index()
    for name in LABELS:
        table[f"{name}_pct"] = (100 * table[name] / table["inspections"]).round(2)
    table["compare"] = table["inspections"] >= MIN_INSPECTIONS
    return table.sort_values(["inspections", *groups], ascending=[False] + [True] * len(groups)).reset_index(drop=True)


by_nta = rates(["nta", "nta_name"])
by_nta.loc[by_nta["nta"] == "", "compare"] = False
by_cuisine = rates(["cuisine"])
by_cuisine.loc[by_cuisine["cuisine"] == "Unknown", "compare"] = False


# 4. Report samples: the 5 biggest groups, the 3 highest rates, the missing group
# and one group below the minimum, so the table shows every kind of row
def sample(table, field):
    big = table.head(5)
    high = table[table["compare"]].sort_values(["any_pest_pct", "inspections"], ascending=False).head(3)
    missing = table[table[field] == ""]
    small = table[~table["compare"] & (table[field] != "")].head(1)
    return pd.concat([big, high, missing, small]).drop_duplicates(field)


summary = pd.DataFrame([
    {"pest": name, "label": label, "inspections": int(visits[name].sum()),
     "pct_inspections": round(100 * visits[name].mean(), 2)}
    for name, label in LABELS.items()
])
print(summary)

save(summary, "q6-pest-summary.csv")
save(by_nta, "q6-by-nta.csv")
save(by_cuisine, "q6-by-cuisine.csv")
save(sample(by_nta, "nta"), "q6-nta-sample.csv")
save(sample(by_cuisine, "cuisine"), "q6-cuisine-sample.csv")
info.update({
    "any_pest": int(visits["any_pest"].sum()),
    "any_pest_pct": round(100 * visits["any_pest"].mean(), 2),
    "missing_nta": int((visits["nta"] == "").sum()),
    "min_inspections": MIN_INSPECTIONS,
})
(OUT_DIR / "q6-summary.json").write_text(json.dumps(info, indent=2) + "\n")
