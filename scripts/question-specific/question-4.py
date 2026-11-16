"""
Q4: do branches of the same chain get similar grades?

Run from the repo root: python3 scripts/question-specific/question-4.py
Finds Dunkin, Starbucks and McDonald's branches by name, takes each branch's current grade
(current_grades in common.py, the same definition as Q2) and counts the grade cards per chain.
Writes src/data/q4-*.csv
"""



import re



import pandas as pd



from common import CARDS, END, FIRST_INSPECTION, START, current_grades, read, save



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



# 3. Current grade of each branch: the grade of its most recent graded inspection, so a later
# N, Z or P replaces an earlier A, B or C. latest_letter keeps that earlier letter for the details
chain_inspections = inspections[inspections["camis"].isin(chains["camis"])]
current = current_grades(chain_inspections).set_index("camis")
for col in ["grade", "card", "grade_date", "latest_letter", "latest_letter_date"]:
    chains[col] = chains["camis"].map(current[col]).fillna("")



# Grade(s) recorded at the most recent inspection, whatever they are (blank if it wasn't graded)
last_date = chain_inspections.groupby("camis")["inspection_date"].max()
on_last = chain_inspections[chain_inspections["inspection_date"] == chain_inspections["camis"].map(last_date)]
on_last = on_last[["camis", "grade"]].replace({"grade": {"": "(missing)"}})
on_last = on_last.drop_duplicates().sort_values(["camis", "grade"])
last_status = on_last.groupby("camis")["grade"].agg(" | ".join)



chains["last_inspection"] = chains["camis"].map(last_date)
chains["last_status"] = chains["camis"].map(last_status)



chains["in_sample"] = chains["in_sample"].astype(bool)



# Dunkin, Starbucks, McDonald's, then the two-brand names
chains["order"] = chains["chain"].map({brand: i for i, brand in enumerate(BRANDS)}).fillna(len(BRANDS))
chains = chains.sort_values(["order", "dba", "camis"])
branches = chains[["chain", "camis", "dba", "boro", "match", "in_sample", "note",
                   "card", "grade", "grade_date", "latest_letter", "latest_letter_date",
                   "last_inspection", "last_status"]]



# 4. Count the cards per chain. Like Q2, the A share is out of the branches that have a grade
# (A, B, C, Grade Pending or Not Yet Graded); branches never graded are counted on their own
rows = []
for brand in BRANDS:
    sample = branches[(branches["chain"] == brand) & branches["in_sample"]]
    counts = sample["card"].value_counts()
    with_grade = sum(counts.get(card, 0) for card in CARDS)
    rows.append({
        "chain": brand,
        "branches": len(sample),
        "A": counts.get("A", 0),
        "B": counts.get("B", 0),
        "C": counts.get("C", 0),
        "grade_pending": counts.get("Grade Pending", 0),
        "not_graded": counts.get("Not Yet Graded", 0),
        "never_graded": len(sample) - with_grade,
        "pct_A": round(100 * counts.get("A", 0) / with_grade, 2),
        "left_out": int(((branches["chain"] == brand) & ~branches["in_sample"]).sum()),
    })
summary = pd.DataFrame(rows)
print(summary)



# 5. Sample for the report: one branch per card (and one never graded) for each chain
picks = []
for brand in BRANDS:
    sample = branches[(branches["chain"] == brand) & branches["in_sample"]]
    for card in CARDS + [""]:
        picks += list(sample[sample["card"] == card].index[:1])



# 6. First inspection scores, same inspections and time window as Q1, Q5 and Q6.
# The card on the door can come after a re-inspection, the first score shows how the visit went
first = inspections[(inspections["inspection_type"] == FIRST_INSPECTION) & inspections["inspection_date"].between(START, END)].copy()
first["score"] = first["score"].astype(int)
scores = first.merge(branches[branches["in_sample"]][["chain", "camis", "dba", "boro"]], on="camis")
scores = scores[["chain", "camis", "dba", "boro", "inspection_date", "score"]].sort_values(["chain", "camis", "inspection_date"])



# one row per chain, plus the whole city to compare with
groups = list(scores.groupby("chain", sort=False))
groups.append(("All restaurants", first))
score_rows = []
for name, group in groups:
    score_rows.append({
        "chain": name,
        "inspections": len(group),
        "branches": group["camis"].nunique(),
        "median_score": group["score"].median(),
        "pct_missed_a": round(100 * (group["score"] > 13).mean(), 2),
        # branches with at least one first inspection over 13 points
        "pct_branches_missed_once": round(100 * group.groupby("camis")["score"].max().gt(13).mean(), 2),
    })
score_summary = pd.DataFrame(score_rows)
print(score_summary)



save(branches, "q4-branches.csv")
save(summary, "q4-chain-summary.csv")
save(branches.loc[picks], "q4-table-sample.csv")
save(scores, "q4-scores.csv")
save(score_summary, "q4-score-summary.csv")
