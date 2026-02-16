# main.py (Version 11 - Render-Ready Paths)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import json
import os
from typing import List, Dict

# --- Config ---
# Paths are now pointing to the persistent disk volume inside the container
DATA_DIR = "/app/data"
FEATURE_STORE_PATH = os.path.join(DATA_DIR, 'feature_store.json')
MODEL_FILENAME = os.path.join(DATA_DIR, 'financial_stress_predictor.pkl')
RL_MODEL_PATH = os.path.join(DATA_DIR, 'intervention_agent_dynamic.zip')
GNN_FEATURES_PATH = os.path.join(DATA_DIR, 'gnn_network_features.csv')
TRANSACTIONS_DB_PATH = os.path.join(DATA_DIR, 'rich_transactions.csv') # The original, full transaction history

FEATURE_NAMES = [
    'feature_late_salary_count', 'feature_decline_week_count', 'feature_lending_app_tx_count',
    'feature_late_utility_count', 'feature_discretionary_spend_ratio', 'feature_atm_withdrawal_count',
    'feature_failed_debit_count', 'network_stress_feature'
]

# --- App & Model Loading ---
app = FastAPI(title="Final Robust Financial Stress API")
predictor_model = None
ALL_TRANSACTIONS = None
# RL Agent and GNN features will also be loaded here
# (Humne RL agent ko pehle hi load kar liya tha, lekin saaf-suthre code ke liye, sab kuch ek saath load karna accha hai)

@app.on_event("startup")
def load_assets():
    global predictor_model, ALL_TRANSACTIONS
    print("--- API Starting Up: Loading all AI assets... ---")
    try:
        # Load the main prediction model
        predictor_model = joblib.load(MODEL_FILENAME)
        print(f"Successfully loaded predictor model from '{MODEL_FILENAME}'")

        # Load the entire transaction history into memory
        ALL_TRANSACTIONS = pd.read_csv(TRANSACTIONS_DB_PATH)
        print(f"Successfully loaded transaction DB from '{TRANSACTIONS_DB_PATH}'")

        print("--- API Ready: All assets loaded successfully. ---")

    except FileNotFoundError as e:
        print(f"--- FATAL API ERROR: An essential asset was not found: {e} ---")
        print("--- The API will not be able to make predictions. Please check your deployment. ---")
        # In a real scenario, you might want the app to exit if a critical file is missing.

# --- API Models ---
class CustomerStateResponse(BaseModel):
    customer_id: str
    financial_stress_score: float
    key_signals: dict
    transaction_history: list


# --- API Endpoint ---
@app.get("/customer/{customer_id}", response_model=CustomerStateResponse)
def get_customer_state_and_predict(customer_id: str):
    # Get feature store
    if not os.path.exists(FEATURE_STORE_PATH):
        raise HTTPException(status_code=404, detail="Feature store not found. Is the consumer running?")
    with open(FEATURE_STORE_PATH, 'r') as f:
        try:
            full_feature_store = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=503, detail="Feature store is busy. Please try again.")
    customer_state = full_feature_store.get(customer_id)
    if not customer_state:
        raise HTTPException(status_code=404, detail=f"No feature state found for {customer_id}.")

    # Predict
    stress_score = -1.0
    if predictor_model:
        input_df = pd.DataFrame([customer_state], columns=FEATURE_NAMES)
        input_df = input_df[FEATURE_NAMES]
        stress_score = predictor_model.predict_proba(input_df)[0, 1]

    # --- THE FIX: Get transaction history from the in-memory DataFrame ---
    customer_transactions = []
    if ALL_TRANSACTIONS is not None:
        customer_transactions = ALL_TRANSACTIONS[ALL_TRANSACTIONS['customer_id'] == customer_id].tail(20).to_dict(
            orient='records')

    # Return everything
    return {
        "customer_id": customer_id,
        "financial_stress_score": stress_score,
        "key_signals": customer_state,
        "transaction_history": customer_transactions
    }
