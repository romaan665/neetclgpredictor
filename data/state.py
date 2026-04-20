import pandas as pd
import re

# ---------------- NORMALIZE ----------------
def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------- CITY → STATE (SINGLE SOURCE OF TRUTH) ----------------
CITY_STATE = {
    # Delhi
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "n delhi": "Delhi",

    # Uttar Pradesh
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh",
    "agra": "Uttar Pradesh",
    "prayagraj": "Uttar Pradesh",
    "allahabad": "Uttar Pradesh",
    "meerut": "Uttar Pradesh",
    "ghaziabad": "Uttar Pradesh",
    "gorakhpur": "Uttar Pradesh",
    "banda": "Uttar Pradesh",
    "raebareli": "Uttar Pradesh",
    "firozabad": "Uttar Pradesh",

    # Maharashtra
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    "wardha": "Maharashtra",
    "chandrapur": "Maharashtra",
    "karad": "Maharashtra",
    "akola": "Maharashtra",

    # Tamil Nadu
    "chennai": "Tamil Nadu",
    "omandurar": "Tamil Nadu",
    "kancheepuram": "Tamil Nadu",
    "chengalpattu": "Tamil Nadu",
    "thiruvannamalai": "Tamil Nadu",
    "tirunelveli": "Tamil Nadu",
    "karur": "Tamil Nadu",

    # Kerala
    "thiruvananthapuram": "Kerala",
    "trivandrum": "Kerala",
    "thrissur": "Kerala",
    "alappuzha": "Kerala",
    "kottayam": "Kerala",
    "kannur": "Kerala",
    "kozhikode": "Kerala",
    "palakkad": "Kerala",

    # Rajasthan
    "jaipur": "Rajasthan",
    "jodhpur": "Rajasthan",
    "kota": "Rajasthan",
    "pali": "Rajasthan",

    # Gujarat
    "ahmedabad": "Gujarat",
    "surat": "Gujarat",
    "vadodara": "Gujarat",
    "baroda": "Gujarat",
    "bhavnagar": "Gujarat",

    # Bihar
    "patna": "Bihar",
    "gaya": "Bihar",

    # West Bengal
    "kolkata": "West Bengal",
    "howrah": "West Bengal",
    "burdwan": "West Bengal",
    "malda": "West Bengal",

    # Odisha
    "bhubaneswar": "Odisha",
    "cuttack": "Odisha",
    "baripada": "Odisha",

    # Punjab
    "amritsar": "Punjab",
    "bathinda": "Punjab",
    "patiala": "Punjab",
    "faridkot": "Punjab",

    # Haryana
    "rohtak": "Haryana",
    "sonepat": "Haryana",
    "faridabad": "Haryana",

    # Others
    "shimla": "Himachal Pradesh",
    "dehradun": "Uttarakhand",
    "ranchi": "Jharkhand",
    "deoghar": "Jharkhand",
    "guwahati": "Assam",
    "agartala": "Tripura",
    "panaji": "Goa",
    "pondicherry": "Puducherry",
    "port blair": "Andaman and Nicobar Islands",
}


# ---------------- EXTRACT STATE ----------------
def extract_state(institute):
    text = normalize_text(institute)

    # 1️⃣ City match (strong)
    for city, state in CITY_STATE.items():
        if city in text:
            return state

    # 2️⃣ Institute keyword fallback
    INSTITUTE_STATE = {
        "jipmer": "Puducherry",
        "aiims guwahati": "Assam",
        "aiims raebareli": "Uttar Pradesh",
        "aiims jodhpur": "Rajasthan",
        "aiims deoghar": "Jharkhand",
        "esic dental college new delhi": "Delhi",
        "maulana azad institute of dental": "Delhi",
        "ims bhu": "Uttar Pradesh",
        "ruhs college": "Rajasthan",
        "nair hospital dental": "Maharashtra",
    }

    for key, state in INSTITUTE_STATE.items():
        if key in text:
            return state

    return "Unknown"


# ---------------- PROCESS FILE ----------------
file_path = "2020_ROUND2.xlsx"
sheets = pd.read_excel(file_path, sheet_name=None)

for sheet, df in sheets.items():
    if "ALLOTTED INSTITUTE" in df.columns:
        df.rename(columns={"ALLOTTED INSTITUTE": "institute_name"}, inplace=True)

    df["state"] = df["institute_name"].apply(extract_state)


# ---------------- PRINT REAL UNKNOWNS ----------------
for sheet, df in sheets.items():
    unknowns = df[df["state"] == "Unknown"]
    if not unknowns.empty:
        print(f"\nUnknown institutes in {sheet}:")
        print(unknowns["institute_name"].unique())


# ---------------- SAVE ----------------
with pd.ExcelWriter("2020-r2-fixed.xlsx", engine="xlsxwriter") as writer:
    for sheet, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet, index=False)
