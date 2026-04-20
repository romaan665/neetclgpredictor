import pandas as pd

file_path = "2020_ROUND2.xlsx"

sheets = pd.read_excel(file_path, sheet_name=None)

all_institutes = set()

for df in sheets.values():
    if "ALLOTTED INSTITUTE" in df.columns:
        all_institutes.update(
            df["ALLOTTED INSTITUTE"]
            .dropna()
            .astype(str)
            .str.strip()
        )

out_df = pd.DataFrame(sorted(all_institutes), columns=["ALLOTTED INSTITUTE"])
out_df.to_excel("unique_allotted_institutes_all_sheets.xlsx", index=False)

print("✅ Saved unique institutes from all sheets")
