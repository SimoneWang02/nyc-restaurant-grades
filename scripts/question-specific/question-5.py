"""
Q5: which violations are cited most often, and what share of citations are critical?

Run from the repo root: python3 scripts/question-specific/question-5.py
Writes src/data/q5-*.csv and q5-summary.json
"""

import json

import pandas as pd

from common import OUT_DIR, load_q5_q6, save

# Short names for the chart. The official descriptions are often two or three sentences
SHORT_LABELS = {
    "10F": "Non-food-contact surfaces",
    "08A": "Pest entry or harborage conditions",
    "06D": "Food-contact surface cleaning",
    "06C": "Food or equipment protection",
    "02G": "Cold holding temperature",
    "04L": "Mice or evidence of mice",
    "10B": "Plumbing and drainage",
    "04N": "Flies or other nuisance pests",
    "04A": "Food Protection Certificate",
    "02B": "Hot holding temperature",
    "06E": "Sanitized equipment or utensil use/storage",
    "04M": "Cockroaches",
    "10G": "Tableware washing and sanitizing",
    "10H": "Single-service articles",
    "04H": "Food adulteration or contamination",
    "05D": "Hand-washing facilities",
    "06F": "Wiping-cloth storage",
    "09A": "Damaged canned food",
    "06H": "HACCP records",
}
FLAGS = ["Critical", "Not Critical", "Other"]

visits, cited, info = load_q5_q6()

# 1. Count citations per code, split by the critical flag on each row.
# Most codes always have the same flag, but a few (e.g. 09A) have both
flag = cited["critical_flag"].where(cited["critical_flag"].isin(FLAGS[:2]), "Other")
counts = pd.crosstab(cited["violation_code"], flag).reindex(columns=FLAGS, fill_value=0)
codes = pd.DataFrame({
    "code": counts.index,
    "critical": counts["Critical"].values,
    "not_critical": counts["Not Critical"].values,
    "other_flag": counts["Other"].values,
})
codes["citations"] = codes[["critical", "not_critical", "other_flag"]].sum(axis=1)

# 2. Share of inspections with the code. Each code appears at most once per inspection,
# so citations = inspections with that code. The denominator includes clean inspections
codes["pct_inspections"] = (100 * codes["citations"] / info["inspections"]).round(2)

# 3. Labels: our short name, plus the most common official wording for the hover text
wording = cited.value_counts(["violation_code", "violation_description"]).reset_index()
description = wording.drop_duplicates("violation_code").set_index("violation_code")["violation_description"]
codes["description"] = codes["code"].map(description)
codes["label"] = [SHORT_LABELS.get(c, d.split(".")[0]) for c, d in zip(codes["code"], codes["description"])]

codes = codes.sort_values(["citations", "code"], ascending=[False, True]).reset_index(drop=True)
codes = codes[["code", "label", "citations", "critical", "not_critical", "other_flag", "pct_inspections", "description"]]

# 4. Critical share over all citations
flags = flag.value_counts().reindex(FLAGS, fill_value=0).rename_axis("flag").reset_index(name="citations")
flags["pct_citations"] = (100 * flags["citations"] / len(cited)).round(2)
print(flags)

# 5. Sample for the report: the 8 most cited codes, 09A (mixed flags) and the rarest code
sample = codes[(codes.index < 8) | (codes["code"] == "09A") | (codes.index == len(codes) - 1)]

save(codes, "q5-code-summary.csv")
save(flags, "q5-critical-summary.csv")
save(sample, "q5-table-sample.csv")
info["codes"] = len(codes)
(OUT_DIR / "q5-summary.json").write_text(json.dumps(info, indent=2) + "\n")
