import camelot
import pandas as pd

writer = pd.ExcelWriter("tables_by_page.xlsx", engine="openpyxl")

table_count = 1
for page in range(1, 2000):  # adjust max page count
    tables = camelot.read_pdf("C:/Users/Alsheefa/Desktop/romi/neetclgpredictor/22.pdf", pages=str(page), flavor="lattice")
    for t in tables:
        t.df.to_excel(writer, sheet_name=f"Table_{table_count}", index=False)
        table_count += 1

writer.close()
print(f"Total tables extracted: {table_count - 1}")
