🩺 NEET College Predictor – Hybrid ML Based Counseling Assistant

A full-stack web application that predicts possible medical colleges for a student based on NEET Rank, Category, Quota, State, and Course using a Hybrid ML model (Rule Logic + XGBoost) trained on 5 years of All-India NEET counseling data.

The system simulates real counseling rounds and classifies colleges into Guaranteed, Possible, and Low-Chance before actual counseling.

🚀 Features
🔐 Login / Signup Authentication
📊 Hybrid ML Model (Rule Logic + XGBoost)
🏫 College prediction for Round 1, 2, 3
📄 Download prediction report as PDF
🌙 Dark / Light Theme UI
👨‍💼 Admin Panel
View database entries
Track user prediction attempts
Block suspicious users
Retrain model with new data
🧹 Data cleaning & normalization of 5 years counseling data
🕸️ (Upcoming) Web crawler to auto-fetch new cutoff PDFs
☁️ Deployment-ready architecture
🧠 How It Works
Collected 5 years of NEET counseling cutoff data (MBBS, BDS, Nursing).
Cleaned and standardized inconsistent institute names and formats.
Stored structured data into MySQL database.
Built FastAPI backend for prediction and authentication APIs.
Developed frontend using HTML, CSS, JavaScript.
Integrated Hybrid ML model for accurate prediction.
Added admin tools for monitoring and retraining.
🛠️ Tech Stack
Layer	Technology Used
Frontend	HTML, CSS, JavaScript
Backend	FastAPI (Python)
Database	MySQL
ML Model	XGBoost + Rule Logic
Tools	Pandas, NumPy, jsPDF
Version Control	GitHub
📂 Project Structure
neetclgpredictor/
│
├── admin-api/        # Admin FastAPI (monitoring, user control, retraining)
├── neet-api/         # Main FastAPI (prediction, auth APIs)
├── cleaned_data/     # Final cleaned Excel datasets (5 years)
├── data/             # Raw collected counseling data
└── README.md
▶️ How to Run Locally
1️⃣ Install dependencies
pip install -r requirements.txt
2️⃣ Run Main API (Prediction)
cd neet-api
uvicorn main:app --reload
3️⃣ Run Admin API
cd admin-api
uvicorn main:app --reload
4️⃣ Open in Browser
http://127.0.0.1:8000
📌 Future Improvements
Automated web crawler to fetch latest cutoff PDFs
Cloud deployment (AWS / Render / Railway)
Institute name auto-standardization pipeline
Real-time database updates
👩‍💻 Developed By

Anusha Manohar – Frontend, Data Cleaning, Integration, Admin Features
Umm E Romaan Shaikh – Database Design, API Development, ML Model, Backend

Internship Project at MGrid Technologies Pvt Ltd

📜 License

This project is developed for academic and research purposes.
