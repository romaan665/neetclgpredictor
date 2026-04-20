from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import pandas as pd
import io
import os
from typing import Optional
import requests
from bs4 import BeautifulSoup

# ===============================
# APP
# ===============================
app = FastAPI(
    title="NEET Admin API",
    description="Admin Panel for NEET Predictor",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # DEV only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===============================
# DATABASE
# ===============================
engine = create_engine(
    "mysql+mysqlconnector://root:romaan665@localhost/neet_counselling",
    pool_pre_ping=True
)


# ===============================
# ADMIN HTML
# ===============================
@app.get("/admin", response_class=HTMLResponse)
def serve_admin():
    path = os.path.join(BASE_DIR, "admin.html")
    if not os.path.exists(path):
        raise HTTPException(500, "admin.html not found")
    return open(path, "r", encoding="utf-8").read()

# ===============================
# DASHBOARD
# ===============================
@app.get("/admin/data-summary")
def data_summary():
    with engine.connect() as conn:
        return {
            "years": conn.execute(
                text("SELECT DISTINCT YEAR FROM cuttoff ORDER BY YEAR DESC")
            ).scalars().all(),
            "courses": conn.execute(
                text("SELECT DISTINCT COURSE FROM cuttoff ORDER BY COURSE")
            ).scalars().all(),
            "total_users": conn.execute(
                text("SELECT COUNT(*) FROM users")
            ).scalar(),
            "total_predictions": conn.execute(
                text("SELECT COALESCE(SUM(predictions_count),0) FROM users")
            ).scalar(),
        }

# ===============================
# USERS (ADMIN)
# ===============================
@app.get("/admin/users")
def list_users():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, full_name, email, phone,
                   predictions_count, is_blocked,
                   neet_marks, hsc_marks, percentage,
                   registration_date, passing_year
            FROM users
            ORDER BY predictions_count DESC
        """))

        return {
            "users": [
                {
                    **dict(r._mapping),
                    "is_blocked": bool(int(r._mapping["is_blocked"]))
                }
                for r in rows
            ]
        }
# ===============================
# TOGGLE BLOCK (ADMIN)
# ===============================
@app.post("/admin/users/{user_id}/toggle-block")
def toggle_block(user_id: int):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT is_blocked FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not row:
            raise HTTPException(404, "User not found")

        new_status = 0 if int(row._mapping["is_blocked"]) == 1 else 1

        conn.execute(
            text("UPDATE users SET is_blocked = :s WHERE id = :id"),
            {"s": new_status, "id": user_id}
        )

    return {"blocked": bool(new_status)}

# ===============================
# 🔒 AUTH + BLOCK DEPENDENCY (CORE FIX)
# ===============================
def get_active_user(
    x_user_id: Optional[int] = Header(None)
):
    """
    Frontend MUST send:
    X-User-Id: <user_id>
    """

    if not x_user_id:
        raise HTTPException(401, "Missing user identity")

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, is_blocked FROM users WHERE id = :id"),
            {"id": x_user_id}
        ).fetchone()

        if not user:
            raise HTTPException(404, "User not found")

        if int(user._mapping["is_blocked"]) == 1:
            raise HTTPException(
                status_code=403,
                detail="Your account has been blocked by admin."
            )

        return user._mapping["id"]

# ===============================
# USER API (BLOCKED USERS STOP HERE)
# ===============================
@app.post("/predict")
def predict(
    data: dict,
    user_id: int = Depends(get_active_user)
):
    return {
        "message": "Prediction successful",
        "user_id": user_id
    }

# ===============================
# UPLOAD CUTOFF
# ===============================
@app.post("/upload-cutoff-file")
async def upload_cutoff_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx allowed")

    content = await file.read()
    xls = pd.ExcelFile(io.BytesIO(content))

    required = [
        "YEAR", "ROUND", "AIR_RANK",
        "COURSE", "INSTITUTE",
        "CATEGORY", "QUOTA", "STATE"
    ]

    total = 0
    errors = []

    with engine.begin() as conn:
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            df.columns = df.columns.str.strip().str.upper()

            # ❌ Check missing columns
            missing = list(set(required) - set(df.columns))
            if missing:
                errors.append({
                    "sheet": sheet,
                    "error": f"Missing columns: {missing}"
                })
                continue

            # ❌ Check datatype issues
            try:
                df = df[required].dropna().drop_duplicates()
                df = df.astype({
                    "YEAR": int,
                    "ROUND": int,
                    "AIR_RANK": int
                })
            except Exception as e:
                errors.append({
                    "sheet": sheet,
                    "error": "Invalid data type (YEAR/ROUND/AIR_RANK must be numbers)"
                })
                continue

            if not df.empty:
                df.to_sql("cuttoff", conn, if_exists="append", index=False)
                total += len(df)

    # 🚨 If errors exist
    if errors:
        return {
            "status": "warning",
            "rows_inserted": total,
            "errors": errors
        }

    if total == 0:
        raise HTTPException(400, "No valid rows found")

    return {
        "status": "success",
        "rows_inserted": total
    }

@app.get("/admin/demo-cutoff-file")
def download_demo_cutoff():
    file_path = os.path.join(BASE_DIR, "static", "demo_cutoff.xlsx")

    if not os.path.exists(file_path):
        raise HTTPException(404, "Demo Excel file not found")

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="demo_cutoff.xlsx"
    )

from urllib.parse import urljoin

@app.post("/admin/crawl-data")
def crawl_data():
    try:
        base_url = "https://www.mcc.nic.in"
        page_url = "https://mcc.nic.in/WebinfoUG/Page/Page?PageId=1&LangId=P"

        headers = {
    "User-Agent": "Mozilla/5.0"
}

        response = requests.get(page_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a", href=True)

        file_links = []

        for link in links:
            href = link["href"]

            if any(ext in href.lower() for ext in [".pdf", ".xlsx", ".xls"]):
                full_url = urljoin(base_url, href)
                file_links.append(full_url)

        file_links = list(set(file_links))[:20]  # max 20 files

        # 📁 create folder
        folder = os.path.join(BASE_DIR, "downloads")
        os.makedirs(folder, exist_ok=True)

        downloaded_files = []

        for url in file_links:
            try:
                filename = url.split("/")[-1]
                filepath = os.path.join(folder, filename)

                res = requests.get(url)

                with open(filepath, "wb") as f:
                    f.write(res.content)

                downloaded_files.append(filename)

            except:
                continue

        return {
            "status": "success",
            "files_downloaded": downloaded_files,
            "count": len(downloaded_files)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }