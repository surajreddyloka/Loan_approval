from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import os
import uuid
from typing import List, Optional

# Import the existing prediction function
from src.predit import make_prediction

app = FastAPI(title="Loan Approval API", version="2.0")

@app.on_event("startup")
def startup_event():
    from database.db_connection import init_db
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing database on startup: {e}")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request and response
class PredictionRequest(BaseModel):
    monthly_income: float = Field(..., gt=0)
    loan_amount: float = Field(..., gt=0)
    existing_debt: float = Field(0, ge=0)
    credit_score: int = Field(..., ge=300, le=850)
    employment_status: str  # e.g., "Employed", "Self-Employed", "Unemployed"
    education_level: str    # e.g., "Graduate", "Not Graduate"
    
    # Optional fields for the UI dashboard (not strictly used by the ML model right now, 
    # but good to capture for completeness and UI validation)
    loan_term: Optional[int] = None
    employment_duration: Optional[float] = None
    savings_amount: Optional[float] = None

class PredictionResponse(BaseModel):
    status: str
    probability: float
    risk_score: float
    loan_id: str
    dti: float
    lti: float
    income_coverage: float
    strengths: List[str]
    risk_factors: List[str]
    recommendations: List[str]

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0"}

@app.post("/api/predict", response_model=PredictionResponse)
def predict_loan(request: PredictionRequest):
    print("Incoming Request:", request.model_dump())
    
    try:
        # Calculate derived metrics
        annual_income = request.monthly_income * 12
        dti = (request.existing_debt / annual_income * 100) if annual_income > 0 else 0
        lti = (request.loan_amount / annual_income) if annual_income > 0 else 0
        income_coverage = (annual_income / request.existing_debt) if request.existing_debt > 0 else 99.0
        
        # Map employment and education to model expectations
        emp_map = {"Employed": 0, "Self-Employed": 1, "Unemployed": 2}
        edu_map = {"Graduate": 1, "Not Graduate": 0}
        
        emp_val = emp_map.get(request.employment_status, 0) # Default Employed
        edu_val = edu_map.get(request.education_level, 0)   # Default Not Graduate
        
        # Prepare input vector for the model
        # [annual_income, credit_score, loan_amount, employment_status_val, education_level_val, existing_debt]
        input_vec = [
            float(annual_income),
            int(request.credit_score),
            float(request.loan_amount),
            int(emp_val),
            int(edu_val),
            float(request.existing_debt),
        ]
        
        loan_id = f"APP-{str(uuid.uuid4())[:8].upper()}"
        
        # Call the existing ML prediction function
        status, prob = make_prediction(input_vec, loan_id)
        
        # Generate Strengths and Risk Factors for the UI
        strengths = []
        risk_factors = []
        recommendations = []
        
        if request.credit_score >= 700:
            strengths.append(f"Strong credit score ({request.credit_score})")
        else:
            risk_factors.append("Low credit score")
            recommendations.append("Improve credit score before reapplying")
            
        if dti <= 35:
            strengths.append(f"Healthy debt-to-income ratio ({dti:.1f}%)")
        else:
            risk_factors.append(f"High debt-to-income ratio ({dti:.1f}%)")
            recommendations.append("Consider paying down existing debt")
            
        if lti <= 3.0:
            strengths.append("Conservative loan-to-income ratio")
        elif lti > 5.0:
            risk_factors.append("Requested loan amount is high relative to income")
            recommendations.append("Consider requesting a smaller loan amount")
            
        if request.employment_status == "Employed":
            strengths.append("Stable employment status")
        elif request.employment_status == "Unemployed":
            risk_factors.append("Currently unemployed")
            
        result = PredictionResponse(
            status=status,
            probability=prob,
            risk_score=1.0 - prob,
            loan_id=loan_id,
            dti=round(dti, 2),
            lti=round(lti, 2),
            income_coverage=round(income_coverage, 2),
            strengths=strengths,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
        print("Prediction Result:", result.model_dump())
        return result
        
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
def get_history():
    from database.db_connection import get_connection
    import pandas as pd
    try:
        conn, db_type = get_connection()
        query = """
            SELECT loan_id, credit_score, annual_income, loan_amount, approval_status
            FROM predictions
            ORDER BY id DESC
            LIMIT 10
        """
        # For SQLite, the wrapper doesn't work perfectly with pandas read_sql_query directly sometimes,
        # but in the original app it accessed conn.conn
        actual_conn = conn.conn if db_type == "SQLite" else conn
        df = pd.read_sql_query(query, actual_conn)
        conn.close()
        
        records = df.to_dict(orient="records")
        return {"history": records}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"history": [], "error": str(e)}

# Mount static files for React frontend in production
# This assumes the React app is built into 'frontend/dist'
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
