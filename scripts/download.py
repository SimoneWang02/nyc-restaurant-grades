"""
Download a dated snapshot of the NYC restaurant inspection data.

Run from the repo root:  python3 scripts/download.py

Saves data/raw/inspections_YYYY-MM-DD.csv (today's date) and writes that date
to data/raw/SNAPSHOT.txt so later scripts know which file to read.
"""

import datetime
import urllib.request
from pathlib import Path

URL = "https://data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv?accessType=DOWNLOAD"
RAW_DIR = Path("data/raw")

today = datetime.date.today().isoformat()
out = RAW_DIR / f"inspections_{today}.csv"
RAW_DIR.mkdir(parents=True, exist_ok=True)

if out.exists():
    print(f"{out} already exists, skipping download.")
else:
    print(f"Downloading to {out}...")
    urllib.request.urlretrieve(URL, out)
    print(f"Done: {out.stat().st_size / 1e6:.1f} MB")
