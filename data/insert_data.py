import pandas as pd
import mysql.connector

# -------------------------------
# CONNECT TO MYSQL DATABASE
# -------------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="romaan665",
    database="cutoff_project"
)

cursor = db.cursor()

# -------------------------------
# FUNCTION TO INSERT A DATAFRAME
# -------------------------------
def insert_sheet(df):
    for _, row in df.iterrows():
        sql = """
        INSERT INTO cutoff_data 
        (college_name, year, college_type, code, course, category, 
         air_first, air_last, marks_first, marks_last)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            str(row["College Name"]),
            str(row["Year"]),
            str(row["College Type"]),
            str(row["Code"]),
            str(row["Course"]),
            str(row["Category"]),
            str(row["AIR First"]),
            str(row["AIR Last"]),
            str(row["Marks First"]),
            str(row["Marks Last"])
        )

        cursor.execute(sql, values)
    db.commit()

# -------------------------------
# READ BOTH YEARS FILES
# -------------------------------
files = ["C:/Users/Alsheefa/Desktop/romi/neetclgpredictor/cutoff23.xlsx", "C:/Users/Alsheefa/Desktop/romi/neetclgpredictor/cutoff24.xlsx"]
sheets = ["MBBS", "BDS", "BAMS", "BHMS", "BUMS"]

for file in files:
    for sheet in sheets:
        print(f"Inserting {file} - {sheet}")
        df = pd.read_excel(file, sheet_name=sheet)
        insert_sheet(df)

print("✅ All data inserted successfully!")
