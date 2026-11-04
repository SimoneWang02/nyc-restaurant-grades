"""
Download the 2010 NTA code -> name list for Q6.

Run from the repo root: python3 scripts/download-nta-lookup.py
The inspection data only has NTA codes like "MN17". The names come from the ntacode and
ntaname columns of DCP's 2010 Census Tracts table:
https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/bmjq-373p
"""

from pathlib import Path

import pandas as pd

URL = ("https://data.cityofnewyork.us/resource/bmjq-373p.csv"
       "?$select=distinct%20ntacode,ntaname&$limit=5000")
OUT_FILE = Path("data/reference/nta-2010.csv")

names = pd.read_csv(URL, dtype=str).rename(columns={"ntacode": "nta", "ntaname": "nta_name"})
names = names.dropna().drop_duplicates().sort_values("nta")
assert not names["nta"].duplicated().any(), "one NTA code has two names"

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
names.to_csv(OUT_FILE, index=False)
print(f"Wrote {OUT_FILE}: {len(names)} NTAs")
