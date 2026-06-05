# 🏦 VaultRisk // AI Credit Risk Assessment System

VaultRisk is a full-stack, AI-powered credit risk scoring and loan eligibility application. Using a trained Machine Learning model, it evaluates applicant financials and provides instant, explainable credit decisions.

The system features a **premium dark-glassmorphism dashboard** built in React, served by a **FastAPI backend**, and backed by an **SQLite/PostgreSQL database** for transaction audit logging.

---

## 🚀 Key Features

* **AI-Powered Underwriting**: Instantly evaluates loan applications and provides approval/rejection predictions with confidence metrics using a decision-tree classifier.
* **Explainable AI (XAI)**: Demystifies model predictions by generating specific applicant strengths, identified risk factors, and actionable improvement recommendations.
* **Real-time Indicators**: Interactive sliders and inputs update key financial risk ratios (Debt-to-Income, Loan-to-Income, and Income Coverage) client-side in real-time.
* **Auditable Log & Analytics**: Stores all historical applications in an audit database, complete with search, decision filters, and aggregate approval stats.
* **Dual-Database Support**: Dynamically connects to PostgreSQL in production with automatic fallback to SQLite for local development.

---

## 🛠️ Tech Stack

* **Frontend**: React (Vite), Vanilla CSS, responsive layouts & custom SVG animations.
* **Backend**: FastAPI (Python), Uvicorn.
* **Machine Learning**: Scikit-Learn (Decision Tree Classifier), Pandas, NumPy, Joblib.
* **Database**: PostgreSQL (psycopg2) with SQLite fallback.
* **Deployment**: Render Web Services (configured via `render.yaml`).

---

## 📂 Directory Structure

```text
├── database/
│   ├── db_connection.py    # Database connection manager (PostgreSQL / SQLite)
│   └── credit_risk.db      # Local SQLite database file (auto-generated)
├── models/
│   └── credit_model.pkl    # Trained Decision Tree classifier model
├── src/
│   ├── predit.py           # ML prediction script & database logging logic
│   ├── preprocess.py       # Data pre-processing helper functions
│   └── train_model.py      # Model training script
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # React application main logic & dashboard UI
│   │   ├── App.css         # Dashboard-specific styles & animations
│   │   └── index.css       # Core typography, resets & theme colors
│   ├── vite.config.js      # Vite dev configuration (with backend routing proxy)
│   └── package.json        # Frontend NPM package configuration
├── main.py                 # FastAPI application & REST API endpoints
├── app.py                  # Streamlit dashboard version (optional fallback)
├── render.yaml             # Render Blueprint infrastructure configuration
└── requirements.txt        # Python backend packages
```

---

## ⚙️ How to Run Locally

### Prerequisites
* Python 3.9+ installed
* Node.js & npm installed

### 1. Database Initialization
Initialize the local SQLite database schema by running:
```bash
python3 database/db_connection.py
```

### 2. Run in Development Mode (Recommended for Editing)
To run the frontend and backend concurrently with hot-reloading:

* **Start the FastAPI Backend**:
  ```bash
  python3 -m uvicorn main:app --port 8000 --reload
  ```
* **Start the React Frontend**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
Open **`http://localhost:5173/`** in your browser. Any UI updates will apply instantly, and API requests will be proxied to port `8000`.

### 3. Run the Production Build Locally
To verify how the application builds and runs in production:
```bash
cd frontend
npm run build
cd ..
python3 -m uvicorn main:app --port 8000
```
Open **`http://localhost:8000/`** to view the app. FastAPI serves the compiled React application directly.

---

## ☁️ Deploying to Render

This repository is pre-configured for deployment using the **Render Blueprint** specification.

1. Push all code to your GitHub repository.
2. Log in to your [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** and select **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically parse the `render.yaml` file, compile the React assets, launch the FastAPI web server, and serve the application publicly.
