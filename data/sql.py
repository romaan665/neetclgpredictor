import pandas as pd
from sqlalchemy import create_engine
import glob
import os

# ========== 1. DATABASE CONFIG (EDIT THIS) ==========
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',              # your MySQL user
    'password': 'romaan665',      # your MySQL password
    'database': 'neet_counselling'
}

# Folder where your Excel files are kept
BASE_PATH = r"C:/Users/Alsheefa/Desktop/romi/neetclgpredictor/cleaned_data"   # ← your folder
# ====================================================

engine = create_engine(
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
)

# find all .xlsx files in that folder
excel_files = glob.glob(os.path.join(BASE_PATH, "*.xlsx"))

print("🚀 Starting import into table `cuttoff`...")
print(f"📁 Folder: {BASE_PATH}")
print(f"📋 Found {len(excel_files)} Excel files.\n")

total_rows = 0
errors = []

for i, fname in enumerate(excel_files, 1):
    print(f"[{i}/{len(excel_files)}] File: {fname}")
    try:
        xl = pd.ExcelFile(fname)
    except Exception as e:
        print(f"  ❌ Cannot open file: {e}")
        errors.append((fname, str(e)))
        continue

    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(fname, sheet_name=sheet)

            # 1) Normalize column names from Excel
            df.columns = df.columns.str.strip().str.upper()

            # 2) Keep columns that match your table EXACTLY
            keep_cols = [
                'YEAR', 'ROUND', 'AIR_RANK',
                'QUOTA', 'INSTITUTE', 'COURSE',
                'CATEGORY', 'STATE'
            ]
            df = df[keep_cols]

            # 3) Insert into MySQL
            df.to_sql('cuttoff', con=engine, if_exists='append', index=False)
            print(f"  ✅ Sheet {sheet}: {len(df)} rows inserted")
            total_rows += len(df)

        except Exception as e:
            print(f"  ❌ Error in sheet {sheet}: {e}")
            errors.append((f"{fname}:{sheet}", str(e)))

print("\n✅ Import finished.")
print(f"📊 Total rows inserted: {total_rows}")
if errors:
    print("\nSome errors occurred:")
    for f, msg in errors:
        print(f"  - {f}: {msg}")
else:
    print("No errors.")
