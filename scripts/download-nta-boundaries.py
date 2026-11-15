"""
Build the 2010 NTA boundaries for the Q2 map.

Run from the repo root: python3 scripts/download-nta-boundaries.py
Needs Node.js: it runs mapshaper through npx.

NYC Open Data no longer has the 2010 NTA boundary file, but DCP's 2010 Census Tracts table
(the same table scripts/download-nta-lookup.py takes the NTA names from) has each tract's
shape and its NTA code. 2010 NTAs are made of whole tracts, so merging the tracts by NTA code
gives the 2010 NTA shapes:
https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/bmjq-373p

Writes src/data/nta-2010.json, a TopoJSON file with one object "ntas" and the properties
nta, nta_name and boro. The tract file is large, so it is saved to data/raw/ (not in git).
"""

import json
import subprocess
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://data.cityofnewyork.us/resource/bmjq-373p.geojson?$limit=5000"
TRACTS_FILE = Path("data/raw/census-tracts-2010.geojson")
OUT_FILE = Path("src/data/nta-2010.json")
NTA_NAMES_FILE = Path("data/reference/nta-2010.csv")
MAPSHAPER = "mapshaper@0.7.96"  # pinned, so the output doesn't change with new releases

# 1. Download the 2010 census tracts, each with its NTA code
TRACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(URL, TRACTS_FILE)
tracts = json.loads(TRACTS_FILE.read_text())["features"]
print(f"Downloaded {len(tracts):,} tracts to {TRACTS_FILE}")

# 2. Merge the tracts of each NTA into one shape, then simplify the outlines.
# mapshaper simplifies shared borders once, so neighboring NTAs still meet without gaps
subprocess.run([
    "npx", "--yes", MAPSHAPER,
    "-i", str(TRACTS_FILE),
    "-dissolve", "ntacode", "copy-fields=ntaname,boroname",
    "-rename-fields", "nta=ntacode,nta_name=ntaname,boro=boroname",
    "-rename-layers", "ntas",
    "-simplify", "10%", "keep-shapes",
    "-o", "format=topojson", "quantization=100000", str(OUT_FILE),
], check=True)

# 3. Check: one shape per NTA, and the same NTA codes as the name lookup
shapes = json.loads(OUT_FILE.read_text())["objects"]["ntas"]["geometries"]
codes = [shape["properties"]["nta"] for shape in shapes]
names = pd.read_csv(NTA_NAMES_FILE, dtype=str)
assert len(codes) == len(set(codes)), "an NTA has more than one shape"
assert set(codes) == set(names["nta"]), "shape codes don't match the NTA name lookup"
print(f"Wrote {OUT_FILE}: {len(shapes)} NTAs, {OUT_FILE.stat().st_size / 1e3:.0f} kB")
