import pandas as pd
import joblib
from sqlalchemy import text
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.engine import Engine
import os

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# -------------------------------------------------
# Train model PER COURSE
# -------------------------------------------------
def train_xgboost_models(engine: Engine):

    query = """
    SELECT
        YEAR,
        ROUND,
        QUOTA,
        INSTITUTE,
        COURSE,
        CATEGORY,
        STATE,
        AIR_RANK
    FROM cuttoff
    """

    df = pd.read_sql(text(query), engine)

    if df.empty or len(df) < 100:
        raise ValueError("Not enough data to train models")

    trained_models = []

    # ---------------------------------------------
    # Train separate model for each course
    # ---------------------------------------------
    for course in df["COURSE"].unique():

        course_df = df[df["COURSE"] == course].copy()

        if len(course_df) < 50:
            continue  # skip small datasets

        # -------------------------------
        # Encode categorical columns
        # -------------------------------
        encoders = {}
        categorical_cols = ["QUOTA", "INSTITUTE", "CATEGORY", "STATE"]

        for col in categorical_cols:
            le = LabelEncoder()
            course_df[col] = le.fit_transform(course_df[col].astype(str))
            encoders[col] = le

        X = course_df.drop(columns=["AIR_RANK", "COURSE"])
        y = course_df["AIR_RANK"]

        # -------------------------------
        # Train XGBoost
        # -------------------------------
        model = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42
        )

        model.fit(X, y)

        # -------------------------------
        # File names (AS YOU REQUESTED)
        # -------------------------------
        safe_course = course.replace(" ", "_").upper()

        model_path = os.path.join(
            MODEL_DIR,
            f"xgb_{safe_course}_delta.pkl"
        )

        encoder_path = os.path.join(
            MODEL_DIR,
            f"xgb_encoders_{safe_course}.pkl"
        )

        # -------------------------------
        # Save artifacts
        # -------------------------------
        joblib.dump(model, model_path)
        joblib.dump(encoders, encoder_path)

        trained_models.append({
            "course": course,
            "rows_used": len(course_df),
            "model_file": model_path,
            "encoder_file": encoder_path
        })

    if not trained_models:
        raise ValueError("No course had enough data to train")

    return trained_models
