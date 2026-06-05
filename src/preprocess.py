import pandas as pd
import numpy as np

def load_data():
    """Loads raw loan data from the local data directory."""
    return pd.read_csv("data/loan_data.csv")

def clean_data(df):
    """
    Enriches and cleans the raw dataset to produce target features:
    - Annual_Income (ApplicantIncome + CoapplicantIncome)
    - Credit_Score (derived from Credit_History)
    - Loan_Amount (scaled to actual USD)
    - Employment_Status_Val (Employed=0, Self-Employed=1, Unemployed=2)
    - Education_Level_Val (Graduate=1, Not Graduate=0)
    - Existing_Debt (realistic DTI-based debt synthesis)
    - Loan_Status (Y=1, N=0)
    """
    # Create a copy to prevent SettingWithCopyWarning
    df = df.copy()

    # Set numpy random seed for fully reproducible data enrichment
    np.random.seed(42)

    # 1. Handle missing ApplicantIncome and CoapplicantIncome and calculate Annual_Income
    df['ApplicantIncome'] = df['ApplicantIncome'].fillna(df['ApplicantIncome'].median())
    df['CoapplicantIncome'] = df['CoapplicantIncome'].fillna(df['CoapplicantIncome'].median())
    df['Annual_Income'] = df['ApplicantIncome'] + df['CoapplicantIncome']

    # 2. Scale LoanAmount to standard USD (CSV has it in thousands)
    loan_amount_median_k = df['LoanAmount'].median()
    df['Loan_Amount'] = df['LoanAmount'].fillna(loan_amount_median_k) * 1000

    # 3. Handle missing Credit_History and synthesize realistic Credit_Score (300 to 850)
    # Fill missing credit history based on loan status (Y typically implies credit history was good)
    df['Credit_History'] = df['Credit_History'].fillna(df['Loan_Status'].map({'Y': 1.0, 'N': 0.0}).fillna(1.0))
    
    credit_scores = []
    for ch in df['Credit_History']:
        if ch == 1.0:
            # Good credit history -> Prime credit score (650 to 850)
            score = np.random.randint(650, 850)
        else:
            # Poor credit history -> Subprime credit score (300 to 649)
            score = np.random.randint(300, 649)
        credit_scores.append(score)
    df['Credit_Score'] = credit_scores

    # 4. Map Self_Employed and clean missing values. Synthesize 5% Unemployment for realism
    df['Self_Employed'] = df['Self_Employed'].fillna('No')
    employment_vals = []
    for se in df['Self_Employed']:
        # 5% chance of being unemployed for interesting scenarios
        if np.random.rand() < 0.05:
            val = 2  # Unemployed
        elif se == 'Yes':
            val = 1  # Self-Employed
        else:
            val = 0  # Employed
        employment_vals.append(val)
    df['Employment_Status_Val'] = employment_vals

    # 5. Map Education to Education_Level_Val
    df['Education'] = df['Education'].fillna('Graduate')
    df['Education_Level_Val'] = df['Education'].map({'Graduate': 1, 'Not Graduate': 0})

    # 6. Synthesize realistic Existing_Debt based on a dynamic DTI ratio (5% to 40% of income)
    debts = []
    for income in df['Annual_Income']:
        dti_ratio = np.random.uniform(0.05, 0.40)
        # Monthly debt * 12 to get annual existing debt
        annual_debt = round(income * dti_ratio, 2)
        debts.append(annual_debt)
    df['Existing_Debt'] = debts

    # 7. Clean and map target variable
    df['Loan_Status'] = df['Loan_Status'].fillna('N')
    df['Loan_Status_Val'] = df['Loan_Status'].map({'Y': 1, 'N': 0})

    return df
