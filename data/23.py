import pandas as pd
import glob

files = glob.glob("*.csv")

dfs = []
for f in files:
    df = pd.read_csv(f)
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

merged.to_csv("neet_cutoff_merged.csv", index=False)

print("✅ Merged CSVs fast")
