"""
Q4: do branches of the same chain get similar grades?

Run from the repo root: python3 scripts/question-specific/question-4.py
Finds Dunkin, Starbucks and McDonald's branches by name, takes each branch's latest
A/B/C grade and counts grades per chain. Writes src/data/q4-*.csv
"""

import re

import pandas as pd

from common import read, save

BRANDS = {"Dunkin": r"DUNKIN", "Starbucks": r"STARBUCKS", "McDonald's": r"MC\s*DONALD"}
# A branch's name starts with the brand ("DUNKIN'", not "THE JUICE HOUSE NEAR DUNKIN")
STARTS_WITH = {"Dunkin": r"^DUNKIN\b", "Starbucks": r"^STARBUCKS\b", "McDonald's": r"^MC\s*DONALD'?S\b"}
# Names that mention a second food brand, e.g. "DUNKIN / BASKIN ROBBINS"
OTHER_BRANDS = r"BASKIN|JIMMY JOHN|POPEYES|PIZZA HUT|SHAKE SHACK|CIBO|ALIDORO|MAMA MIA|PRIME RIB|NATHANS?|PIZZA PUB"
NOT_THE_CHAIN = {"50181887", "40395525"}  # Juice House near Dunkin, McDonald Avenue Diner

restaurants = read("restaurants")
inspections = read("inspections")
decisions = pd.read_csv("data/manual/q4-name-decisions.csv", dtype=str, keep_default_na=False)

# 1. Find restaurants whose name mentions one of the brands
# (some names use a curly ’ instead of ', e.g. DUNKIN’)
restaurants["name"] = restaurants["dba"].str.upper().str.replace("’", "'").str.strip()
restaurants["brands"] = restaurants["name"].apply(lambda n: [b for b, p in BRANDS.items() if re.search(p, n)])
chains = restaurants[restaurants["brands"].str.len() > 0].copy()
chains["chain"] = chains["brands"].str.join(" | ")


# 2. Decide which matches count as a branch of that chain
def match(row):
    name = row["name"]
    if row["camis"] in NOT_THE_CHAIN:
        return "not this chain"
    if len(row["brands"]) > 1 or re.search(OTHER_BRANDS, name):
        return "two brands"
    if "/" in name or "CHARTWELLS" in name:
        return "check by hand"  # usually a concession or a shared counter
    if re.search(STARTS_WITH[row["brands"][0]], name):
        return "branch"
    return "brand not first"


chains["match"] = chains.apply(match, axis=1)
chains["in_sample"] = chains["match"] == "branch"
chains["note"] = ""

# The 12 "check by hand" records were looked up one by one (data/manual/q4-name-decisions.csv)
checked = chains.merge(decisions, on="camis", how="inner", suffixes=("", "_checked"))
assert (checked["dba"] == checked["dba_checked"]).all(), "a checked restaurant changed its name, look at it again"
is_checked = chains["camis"].isin(decisions["camis"])
chains.loc[is_checked, "match"] = "checked by hand"
chains.loc[is_checked, "in_sample"] = chains.loc[is_checked, "camis"].map(decisions.set_index("camis")["in_sample"].eq("true"))
chains.loc[is_checked, "note"] = chains.loc[is_checked, "camis"].map(decisions.set_index("camis")["reason"])

# 3. Latest A/B/C grade for each branch, by grade date then inspection date.
# A later N/Z/P (not graded yet / pending) does not replace it; we keep it as last_status
chain_inspections = inspections[inspections["camis"].isin(chains["camis"])]
letters = chain_inspections[chain_inspections["grade"].isin(["A", "B", "C"]) & (chain_inspections["grade_date"] != "")]
letters = letters.sort_values(["camis", "grade_date", "inspection_date"])
latest = letters.groupby("camis").tail(1)

# Check: no branch has two different letters on its latest date
same_day = letters.merge(latest[["camis", "grade_date", "inspection_date"]])
assert same_day.groupby("camis")["grade"].nunique().max() == 1, "two letters on the same latest date"

# Grade(s) recorded at the most recent inspection, whatever they are
last_date = chain_inspections.groupby("camis")["inspection_date"].max()
on_last = chain_inspections[chain_inspections["inspection_date"] == chain_inspections["camis"].map(last_date)]
on_last = on_last[["camis", "grade"]].replace({"grade": {"": "(missing)"}})
on_last = on_last.drop_duplicates().sort_values(["camis", "grade"])
last_status = on_last.groupby("camis")["grade"].agg(" | ".join)

chains["grade"] = chains["camis"].map(latest.set_index("camis")["grade"]).fillna("")
chains["grade_date"] = chains["camis"].map(latest.set_index("camis")["grade_date"]).fillna("")
chains["last_inspection"] = chains["camis"].map(last_date)
chains["last_status"] = chains["camis"].map(last_status)

chains["in_sample"] = chains["in_sample"].astype(bool)

# Dunkin, Starbucks, McDonald's, then the two-brand names
chains["order"] = chains["chain"].map({brand: i for i, brand in enumerate(BRANDS)}).fillna(len(BRANDS))
chains = chains.sort_values(["order", "dba", "camis"])
branches = chains[["chain", "camis", "dba", "boro", "match", "in_sample", "note",
                   "grade", "grade_date", "last_inspection", "last_status"]]

# 4. Count grades per chain. The A share only uses branches that have a letter
rows = []
for brand in BRANDS:
    sample = branches[(branches["chain"] == brand) & branches["in_sample"]]
    counts = sample["grade"].value_counts()
    graded = sum(counts.get(g, 0) for g in "ABC")
    rows.append({
        "chain": brand,
        "branches": len(sample),
        "A": counts.get("A", 0),
        "B": counts.get("B", 0),
        "C": counts.get("C", 0),
        "no_grade": len(sample) - graded,
        "pct_A": round(100 * counts.get("A", 0) / graded, 2),
        "left_out": int(((branches["chain"] == brand) & ~branches["in_sample"]).sum()),
    })
summary = pd.DataFrame(rows)
print(summary)

# 5. Sample for the report: one branch per grade (and one without a grade) for each chain
picks = []
for brand in BRANDS:
    sample = branches[(branches["chain"] == brand) & branches["in_sample"]]
    for grade in ["A", "B", "C", ""]:
        picks += list(sample[sample["grade"] == grade].index[:1])

save(branches, "q4-branches.csv")
save(summary, "q4-chain-summary.csv")
save(branches.loc[picks], "q4-table-sample.csv")
