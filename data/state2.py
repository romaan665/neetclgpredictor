import pandas as pd
import re

# ================= NORMALIZE =================
def clean(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ================= STATES =================
STATES = {
    "andhra pradesh": "Andhra Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "delhi": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "puducherry": "Puducherry",
    "jammu": "Jammu and Kashmir",
    "kashmir": "Jammu and Kashmir",
    "andaman": "Andaman and Nicobar Islands",
}


# ================= CITY → STATE =================
# (Your big CITY_STATE dict goes here — KEEP IT)
CITY_STATE = {...}   # ← keep exactly what you built earlier


# ================= AIIMS / SPECIAL RULES =================
AIIMS_RULES = {
    "aiims bathinda": "Punjab",
    "aiims bilaspur": "Himachal Pradesh",
    "aiims guwahati": "Assam",
    "aiims jammu": "Jammu and Kashmir",
    "aiims mangalagiri": "Andhra Pradesh",
    "aiims rajkot": "Gujarat",
    "aiims bibinagar": "Telangana",
    "aiims bhubaneswar": "Odisha",
    "aiims deoghar": "Jharkhand",
    "aiims gorakhpur": "Uttar Pradesh",
    "aiims jodhpur": "Rajasthan",
    "aiims kalyani": "West Bengal",
    "aiims nagpur": "Maharashtra",
    "aiims patna": "Bihar",
    "aiims rai bareli": "Uttar Pradesh",
    "aiims raipur": "Chhattisgarh",
    "aiims rishikesh": "Uttarakhand",
    "aiims bhopal": "Madhya Pradesh",
    "aiims new delhi": "Delhi",
}


# ================= EXTRACT STATE =================
def extract_state(text):
    text = clean(text)

    # 1️⃣ Direct state name
    for key, state in STATES.items():
        if key in text:
            return state

    # 2️⃣ AIIMS rules
    for key, state in AIIMS_RULES.items():
        if key in text:
            return state

    # 3️⃣ City match (anywhere in string)
    for city, state in CITY_STATE.items():
        if city in text:
            return state

    return "Unknown"


# ================= FILE PROCESS =================
file_path = "2020_ROUND2.xlsx"
sheets = pd.read_excel(file_path, sheet_name=None)

for sheet, df in sheets.items():
    if "ALLOTTED INSTITUTE" in df.columns:
        df["state"] = df["ALLOTTED INSTITUTE"].apply(extract_state)

# ================= CHECK UNKNOWNS =================
for sheet, df in sheets.items():
    unknowns = df[df["state"] == "Unknown"]
    if not unknowns.empty:
        print(f"\nUnknown in {sheet}:")
        print(unknowns["ALLOTTED INSTITUTE"].unique())

# ================= SAVE =================
with pd.ExcelWriter("2020-r2.xlsx", engine="xlsxwriter") as writer:
    for sheet, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet, index=False)

print("✅ DONE — states added")
