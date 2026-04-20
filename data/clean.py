import pandas as pd

df = pd.read_excel("2023-r3.xlsx", header=1)

round3 = df.iloc[:, 10:17].copy()

round3.columns = [
    "Allotted Quota",
    "Allotted Institute",
    "Course",
    "Allotted Category",
    "Candidate Category",
    "Option No",
    "Remarks"
]

round3 = round3.dropna(how="all")

round3.to_csv("round3_clean.csv", index=False)

print("✅ Round 3 cleaned & saved")
