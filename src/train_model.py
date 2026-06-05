import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# Ensure current directory is in python path to run from any cwd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.preprocess import load_data, clean_data

def train_decision_tree():
    print("--------------------------------------------------")
    print("Starting Model Training Pipeline (Decision Tree)...")
    print("--------------------------------------------------")
    
    # 1. Load data
    print("Loading data...")
    raw_df = load_data()
    print(f"Raw dataset shape: {raw_df.shape}")

    # 2. Preprocess and enrich data
    print("Enriching and cleaning dataset with target features...")
    df_cleaned = clean_data(raw_df)
    
    # Define features and target
    features = [
        'Annual_Income', 
        'Credit_Score', 
        'Loan_Amount', 
        'Employment_Status_Val', 
        'Education_Level_Val', 
        'Existing_Debt'
    ]
    target = 'Loan_Status_Val'
    
    X = df_cleaned[features]
    y = df_cleaned[target]
    
    print(f"Features: {features}")
    print(f"Target: {target}")
    
    # 3. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set size: {X_train.shape[0]}")
    print(f"Testing set size: {X_test.shape[0]}")
    
    # 4. Train Decision Tree Classifier
    # We set max_depth and min_samples_leaf to prevent overfitting and ensure clean, explainable decision boundaries
    print("Training Decision Tree model...")
    model = DecisionTreeClassifier(
        max_depth=5, 
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 5. Evaluate Model
    print("\nEvaluating model performance on test set...")
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    
    # 6. Feature Importances
    print("\nFeature Importances:")
    importances = model.feature_importances_
    for name, importance in zip(features, importances):
        print(f"  {name:25}: {importance:.4f}")
        
    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)
    
    # 7. Save model
    model_path = "models/credit_model.pkl"
    print(f"\nSaving trained model to: {model_path}")
    joblib.dump(model, model_path)
    print("Model saved successfully!")
    print("--------------------------------------------------")

if __name__ == "__main__":
    train_decision_tree()
