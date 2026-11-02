import pandas as pd
from pathlib import Path

raw = sorted(Path("data/raw").glob("inspections_*.csv"))[-1]
df = pd.read_csv(raw, dtype=str)
print("Using", raw.name)

print(df.shape)
print(df.columns.tolist())