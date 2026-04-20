import pandas as pd

input_file = r"C:/Users/Alsheefa/Desktop/romi/neetclgpredictor/2023-r3.xlsx"
output_file = r"C:/Users/Alsheefa/Desktop/romi/neetclgpredictor/2023-r3_upper.xlsx"

# Read ALL sheets
all_sheets = pd.read_excel(input_file, sheet_name=None, header=None)

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    for sheet_name, df in all_sheets.items():
        # Convert all text to uppercase
        df = df.applymap(lambda x: x.upper() if isinstance(x, str) else x)

        # Write back each sheet
        df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False,
            header=False
        )

print("✅ ALL sheets converted to UPPERCASE")
