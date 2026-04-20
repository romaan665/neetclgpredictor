from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import pandas as pd
import joblib
import os
import traceback
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

import re

def normalize_college(name):
    name = name.upper()
    name = re.sub(r"\s+", " ", name)

    # remove address part
    name = name.split(",")[0]

    # cut after "MEDICAL COLLEGE"
    name = re.sub(r"(MEDICAL COLLEGE).*", r"\1", name)

    return name.strip()


# Base directory of your API
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Old models (your main API models folder)
OLD_MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")

# New models (admin panel training folder)
NEW_MODEL_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "admin-api", "ml", "models")
)
import re


# =================================================
# App
# =================================================
app = FastAPI(
    title="NEET Student Prediction API",
    description="Signup, Login & Round-wise College Prediction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEV ONLY
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    return Path("static/index.html").read_text(encoding="utf-8")

@app.get("/login", response_class=HTMLResponse)
def serve_login():
    return Path("static/login.html").read_text(encoding="utf-8")

@app.get("/signup", response_class=HTMLResponse)
def serve_signup():
    return Path("static/signup.html").read_text(encoding="utf-8")

# =================================================
# Database
# =================================================
engine = create_engine(
    "mysql+mysqlconnector://root:romaan665@localhost/neet_counselling",
    pool_pre_ping=True
)

# =================================================
# Password Hashing
# =================================================
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

# =================================================
# PATH SETUP
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")

MODEL_PATH = os.path.join(MODEL_DIR, "neet_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoders.pkl")

# -------------------------------
# LOAD MODEL + ENCODERS
# -------------------------------
model = joblib.load(MODEL_PATH)
encoders = joblib.load(ENCODER_PATH)

def preprocess_input(data):
    for col in encoders:
        if data[col] not in encoders[col].classes_:
            raise ValueError(f"Invalid value for {col}: {data[col]}")
        
        data[col] = encoders[col].transform([data[col]])[0]

    return list(data.values())


# =================================================
# Utils
# =================================================
def normalize_course(course: str) -> str:
    c = course.strip().upper().replace(".", "").replace(" ", "")
    if c == "MBBS":
        return "MBBS"
    if c == "BDS":
        return "BDS"
    if c in ("NURSING", "BSCNURSING"):
        return "B.SC. NURSING"
    raise HTTPException(400, "Course not supported")

def norm(txt: str) -> str:
    return txt.strip().upper()

def chance_label_from_gap(gap: int) -> str:
    if gap >= 10000:
        return "SAFE"
    elif gap >= 3000:
        return "POSSIBLE"
    else:
        return "RISKY"


# =================================================
# MODEL LOADER
# =================================================
# =================================================
# MODEL LOADER (SIMPLIFIED)
# =================================================
def load_model_bundle(course: str):
    try:
        model_path = os.path.join(OLD_MODEL_DIR, "neet_model.pkl")
        encoder_path = os.path.join(OLD_MODEL_DIR, "encoders.pkl")

        if not os.path.exists(model_path) or not os.path.exists(encoder_path):
            raise HTTPException(503, "Model not found")

        model = joblib.load(model_path)
        encoders = joblib.load(encoder_path)

        return model, encoders, "MAIN"

    except Exception as e:
        raise HTTPException(500, f"Error loading model: {str(e)}")

# =================================================
# Schemas
# =================================================
class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    neet_marks: int
    hsc_marks: int
    percentage: float
    registration_date: str
    passing_year: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class StudentRequest(BaseModel):
    air_rank: int
    course: str
    category: str
    state: str
    quota: str

# =================================================
# BLOCK CHECK
# =================================================
def ensure_user_not_blocked(user_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_blocked FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

    if not row:
        raise HTTPException(404, "User not found")

    if int(row._mapping["is_blocked"]) == 1:
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked by admin."
        )

# =================================================
# SIGNUP
# =================================================
@app.post("/signup")
def signup(user: SignupRequest):
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (
                        full_name, email, phone, password_hash,
                        neet_marks, hsc_marks, percentage,
                        registration_date, passing_year
                    )
                    VALUES (
                        :full_name, :email, :phone, :password_hash,
                        :neet_marks, :hsc_marks, :percentage,
                        :registration_date, :passing_year
                    )
                """),
                {
                    "full_name": user.full_name.strip(),
                    "email": user.email.lower(),
                    "phone": user.phone.strip(),
                    "password_hash": hash_password(user.password),

                    "neet_marks": user.neet_marks,
                    "hsc_marks": user.hsc_marks,
                    "percentage": user.percentage,
                    "registration_date": user.registration_date,
                    "passing_year": user.passing_year,
                }
            )
        
    except IntegrityError:
        raise HTTPException(400, "Email already registered")
    
    return {"status": "success"}

# =================================================
# LOGIN (BLOCK ENFORCED)
# =================================================
@app.post("/login")
def login(user: LoginRequest):
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, full_name, email, password_hash, is_blocked
                FROM users
                WHERE email = :email
            """),
            {"email": user.email.lower()}
        ).fetchone()

    if not row or not verify_password(user.password, row._mapping["password_hash"]):
        raise HTTPException(401, "Invalid email or password")

    if int(row._mapping["is_blocked"]) == 1:
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked by admin."
        )

    return {
        "status": "success",
        "user": {
            "id": row._mapping["id"],
            "name": row._mapping["full_name"],
            "email": row._mapping["email"]
        }
    }
import secrets
from datetime import datetime, timedelta

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)
# ---------------- MODELS (ADD HERE) ----------------
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ---------------- FORGOT PASSWORD ----------------
@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=15)

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": req.email.lower()}
        ).fetchone()

        if not row:
            return {"status": "ok"}

        conn.execute(
            text("""
                UPDATE users
                SET reset_token = :token,
                    reset_token_expiry = :expiry
                WHERE email = :email
            """),
            {
                "token": token,
                "expiry": expiry,
                "email": req.email.lower()
            }
        )

    # ✅ CREATE MESSAGE FIRST
    reset_link = f"http://127.0.0.1:8000/reset-password?token={token}"

    message = MessageSchema(
        subject="Password Reset",
        recipients=[req.email],
        body=f"""
        <h3>Password Reset</h3>
        <p>Click below link:</p>
        <a href="{reset_link}">{reset_link}</a>
        """,
        subtype="html"
    )

    # ✅ SEND EMAIL WITH ERROR LOG
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        print("EMAIL SENT ✅")
    except Exception as e:
        print("EMAIL ERROR ❌:", e)

    return {"status": "ok"}

# ---------------- RESET PAGE ----------------
@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(token: str):
    html = Path("static/reset-password.html").read_text()
    return html.replace("{{token}}", token)


# ---------------- RESET PASSWORD ----------------
@app.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    if len(req.new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT id
                FROM users
                WHERE reset_token = :token
                  AND reset_token_expiry > :now
            """),
            {
                "token": req.token,
                "now": datetime.utcnow()
            }
        ).fetchone()

        if not row:
            raise HTTPException(400, "Invalid or expired token")

        conn.execute(
            text("""
                UPDATE users
                SET password_hash = :pwd,
                    reset_token = NULL,
                    reset_token_expiry = NULL
                WHERE id = :id
            """),
            {
                "pwd": hash_password(req.new_password),
                "id": row._mapping["id"]
            }
        )

    return {"status": "password updated"}

# =================================================
# PREDICT (BLOCK + 422 FIXED)
# =================================================
@app.post("/predict")
def predict(
    req: StudentRequest,
    x_user_id: int | None = Header(default=None, alias="X-User-Id")
):
    if x_user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Missing X-User-Id header"
        )

    ensure_user_not_blocked(x_user_id)

    course = normalize_course(req.course)
    state = norm(req.state)
    quota = norm(req.quota)

    model_source = "MAIN"
    reference_rank = 0

    with engine.connect() as conn:
        years = conn.execute(
            text("""
                SELECT DISTINCT YEAR
                FROM cuttoff
                ORDER BY YEAR DESC
                LIMIT 5
            """)
        ).scalars().all()

        query = (
            text("""
                SELECT YEAR, ROUND, INSTITUTE,college_id, CATEGORY, QUOTA, STATE
                FROM cuttoff
                WHERE YEAR IN :years
                  AND COURSE = :course
                  AND CATEGORY = :category
                  AND STATE = :state
                  AND QUOTA LIKE CONCAT('%', :quota, '%')
            """)
            .bindparams(bindparam("years", expanding=True))
        )

        df = pd.read_sql(
            query,
            conn,
            params={
                "years": list(years),
                "course": course,
                "category": req.category,
                "state": state,
                "quota": quota
            }
        )

    if df.empty:
        raise HTTPException(404, "No colleges found")

    for col in ["college_id", "CATEGORY", "QUOTA", "STATE"]:
        df = df[df[col].isin(encoders[col].classes_)]

    if df.empty:
        raise HTTPException(404, "No colleges match trained data")

    X = pd.DataFrame({
    "YEAR": df["YEAR"],
    "ROUND": df["ROUND"],
    "QUOTA": encoders["QUOTA"].transform(df["QUOTA"]),
    "college_id": encoders["college_id"].transform(df["college_id"]),
    "COURSE": encoders["COURSE"].transform([course] * len(df)),
    "CATEGORY": encoders["CATEGORY"].transform(df["CATEGORY"]),
    "STATE": encoders["STATE"].transform(df["STATE"]),
})

    # ===== Predict FIRST =====
    df["predicted_closing_rank"] = (
        model.predict(X) + reference_rank
    ).astype(int)

    df["predicted_closing_rank"] = df["predicted_closing_rank"].clip(lower=1)

    # ===== THEN filter =====
    MAX_REASONABLE_RANK = req.air_rank + 30000
    df = df[df["predicted_closing_rank"] <= MAX_REASONABLE_RANK]


    # 1️⃣ Clamp invalid ranks
    df["predicted_closing_rank"] = df["predicted_closing_rank"].clip(lower=1)

    # 2️⃣ Normalize institute FIRST

    df["college_id"] = df["college_id"].apply(normalize_college)
    df = (
    df.sort_values("predicted_closing_rank")
    .drop_duplicates(subset=["college_id"], keep="first")
)

    # 4️⃣ Gap logic (single source of truth)
    df["gap"] = df["predicted_closing_rank"] - req.air_rank

    eligible = df[df["gap"] >= 0].copy()
    
    no_chance = df[df["gap"] < 0].copy()

    

    df["INSTITUTE"] = df["college_id"]
    no_chance["INSTITUTE"] = no_chance["college_id"]

    results = {"round_1": [], "round_2": [], "round_3": [], "no_chance": []}

    df = (
        df.sort_values(["college_id", "ROUND"])
        .drop_duplicates(subset=["college_id"], keep="first")
)
    # 6️⃣ Round-wise selection
    for r in [1, 2, 3]:
        temp = eligible[eligible["ROUND"] == r].copy()

        if not temp.empty:
            temp["chance"] = temp["gap"].apply(chance_label_from_gap)

            temp = temp.rename(columns={"college_id": "INSTITUTE"})

            results[f"round_{r}"] = (
                temp.sort_values("gap")
                .head(10)
                [["INSTITUTE", "predicted_closing_rank", "chance"]]
                .to_dict(orient="records")
            )

    # 7️⃣ No-chance list
    if not no_chance.empty:
        no_chance = no_chance.copy()
        no_chance["INSTITUTE"] = no_chance["college_id"]
        no_chance["chance"] = "NO CHANCE"

        results["no_chance"] = (
            no_chance.sort_values("gap", ascending=True)
            .head(10)
            [["INSTITUTE", "predicted_closing_rank", "chance"]]
            .to_dict(orient="records")
        )

    # =============================
    # INCREMENT PREDICTION COUNT
    # =============================
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE users
                SET predictions_count = predictions_count + 1
                WHERE id = :id
            """),
            {"id": x_user_id}
        )
    
    return {
        "model_source": model_source,
        "years_used": sorted(years),
        "course": course,
        "category": req.category,
        "state": state,
        "quota": quota,
        "student_rank": req.air_rank,
        "results": results
    }
