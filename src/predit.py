import os
import sys
import joblib
import numpy as np

# Ensure current directory is in python path to run from any cwd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

# Load trained model — path relative to this file so it works from any working directory
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_PATH = os.path.join(_BASE_DIR, "models", "credit_model.pkl")
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Please run src/train_model.py first.")

def make_prediction(input_data, loan_id):
    """
    Makes a loan approval prediction using the trained Decision Tree model.
    
    Parameters:
    - input_data: list or 1D array of 6 features in order:
      [annual_income, credit_score, loan_amount, employment_status_val, education_level_val, existing_debt]
    - loan_id: string or int, unique identifier for the loan application.
    
    Returns:
    - status: "Approved" or "Rejected"
    - probability: float, probability of approval (class 1)
    """
    import pandas as pd
    features = [
        'Annual_Income', 
        'Credit_Score', 
        'Loan_Amount', 
        'Employment_Status_Val', 
        'Education_Level_Val', 
        'Existing_Debt'
    ]
    # Convert input to DataFrame with feature names to suppress sklearn warning
    input_df = pd.DataFrame([input_data], columns=features)

    # Predict class (0 or 1)
    prediction = model.predict(input_df)[0]

    # Predict probability of approval (class 1)
    probability = float(model.predict_proba(input_df)[0][1])

    # Convert to readable format
    if prediction == 1:
        status = "Approved"
    else:
        status = "Rejected"

    # Map numerical representations to readable text for database audit
    emp_mapping = {0: "Employed", 1: "Self-Employed", 2: "Unemployed"}
    edu_mapping = {0: "Not Graduate", 1: "Graduate"}
    
    emp_str = emp_mapping.get(int(input_data[3]), "Unknown")
    edu_str = edu_mapping.get(int(input_data[4]), "Unknown")

    # Connect to the database (dual backend: PostgreSQL fallback to SQLite)
    conn, db_type = get_connection()
    cursor = conn.cursor()

    # Save complete applicant and prediction records into the database
    cursor.execute(
        """
        INSERT INTO predictions (
            loan_id, annual_income, credit_score, loan_amount, 
            employment_status, education_level, existing_debt, 
            approval_status, risk_score, model_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(loan_id),
            float(input_data[0]),
            int(input_data[1]),
            float(input_data[2]),
            emp_str,
            edu_str,
            float(input_data[5]),
            status,
            probability,
            "v2.0-decision-tree"
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Prediction logged successfully to {db_type} database!")

    return status, probability


if __name__ == "__main__":
    # Sample Input:
    # 1. Annual Income = $75,000
    # 2. Credit Score = 720
    # 3. Loan Amount = $150,000
    # 4. Employment Status = 0 (Employed)
    # 5. Education Level = 1 (Graduate)
    # 6. Existing Debt = $15,000
    sample_input = [75000.0, 720, 150000.0, 0, 1, 15000.0]
    test_loan_id = "TEST-LP001"

    status, prob = make_prediction(sample_input, test_loan_id)

    print("\n--- Inference Test Results ---")
    print(f"Loan ID:          {test_loan_id}")
    print(f"Status:           {status}")
    print(f"Approval Prob:    {prob:.4f}")
    print("------------------------------")
