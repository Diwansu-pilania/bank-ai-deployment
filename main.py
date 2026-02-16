# main.py (Version 12 - Final, Render-Ready, Single Service)
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import json
import os
from typing import List, Dict
import numpy as np
from stable_baselines3 import PPO
import time

# --- Config (Simple Paths for Single Service) ---
FEATURE_STORE_PATH = 'feature_store.json'
MODEL_FILENAME = 'financial_stress_predictor.pkl'
RL_MODEL_PATH = 'intervention_agent_dynamic.zip'
TRANSACTIONS_DB_PATH = 'rich_transactions.csv'
GNN_FEATURES_PATH = 'gnn_network_features.csv'

FEATURE_NAMES = [
    'feature_late_salary_count', 'feature_decline_week_count', 'feature_lending_app_tx_count',
    'feature_late_utility_count', 'feature_discretionary_spend_ratio', 'feature_atm_withdrawal_count',
    'feature_failed_debit_count', 'network_stress_feature'
]

# --- App & Model Loading ---
app = FastAPI(title="Final Robust Financial Stress API")
predictor_model = None
intervention_agent = None
ALL_TRANSACTIONS = None

# --- Retry logic for reading files ---
def read_with_retry(filepath, read_func, retries=5, delay=0.2):
    for i in range(retries):
        try:
            return read_func(filepath)
        except (json.JSONDecodeError, pd.errors.ParserError, FileNotFoundError) as e:
            print(f"Warning: Attempt {i+1} failed to read {filepath}. Retrying in {delay}s. Error: {e}")
            time.sleep(delay)
    raise Exception(f"FATAL: Could not read file {filepath} after {retries} attempts.")

@app.on_event("startup")
def load_assets():
    global predictor_model, intervention_agent, ALL_TRANSACTIONS
    print("--- API Starting Up: Loading all AI assets... ---")
    try:
        predictor_model = read_with_retry(MODEL_FILENAME, joblib.load)
        print(f"Successfully loaded predictor model from '{MODEL_FILENAME}'")

        intervention_agent = read_with_retry(RL_MODEL_PATH, PPO.load)
        print(f"Successfully loaded RL agent from '{RL_MODEL_PATH}'")

        ALL_TRANSACTIONS = read_with_retry(TRANSACTIONS_DB_PATH, pd.read_csv)
        print(f"Successfully loaded transaction DB from '{TRANSACTIONS_DB_PATH}'")

        print("--- API Ready: All assets loaded successfully. ---")
    except Exception as e:
        print(f"--- FATAL API ERROR: An essential asset was not found or is corrupted: {e} ---")
        print("--- The API will not be able to function correctly. Please check your deployment. ---")

# --- Pydantic Models for API ---
class KeySignals(BaseModel):
    feature_late_salary_count: int
    feature_decline_week_count: int
    feature_lending_app_tx_count: int
    feature_late_utility_count: int
    feature_discretionary_spend_ratio: float
    feature_atm_withdrawal_count: int
    feature_failed_debit_count: int
    network_stress_feature: float

class CustomerStateResponse(BaseModel):
    customer_id: str
    financial_stress_score: float
    recommended_action: str
    key_signals: KeySignals
    recent_transactions: List[Dict]

# --- API Endpoint ---
@app.get("/customer/{customer_id}", response_model=CustomerStateResponse)
def get_customer_state_and_predict(customer_id: str):
    if not os.path.exists(FEATURE_STORE_PATH):
        raise HTTPException(status_code=404, detail="Feature store not found. Is the consumer running?")

    # Read the latest state from the feature store
    feature_store = read_with_retry(FEATURE_STORE_PATH, lambda p: json.load(open(p)))
    current_state = feature_store.get(customer_id)

    if not current_state:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found in feature store.")

    # Predict using the loaded model
    stress_score = -1.0
    if predictor_model:
        input_data = pd.DataFrame([current_state], columns=FEATURE_NAMES)
        stress_score = predictor_model.predict_proba(input_data)[0, 1]

    # Get intervention from the RL agent
    recommended_action = "No Action (Agent Offline)"
    if intervention_agent:
        # The observation for the RL agent is the stress score + the 8 features
        observation = [stress_score] + [current_state.get(fn, 0) for fn in FEATURE_NAMES]
        action, _ = intervention_agent.predict(observation, deterministic=True)
        actions_map = {0: "Do Nothing", 1: "Send SMS Nudge", 2: "Send Email Offer", 3: "Flag for Human Call"}
        recommended_action = actions_map.get(action.item(), "Unknown Action")

    # Get recent transactions for the dashboard
    recent_transactions = []
    if ALL_TRANSACTIONS is not None:
        customer_txs = ALL_TRANSACTIONS[ALL_TRANSACTIONS['customer_id'] == customer_id]
        recent_transactions = customer_txs.tail(20).to_dict(orient='records')

    return CustomerStateResponse(
        customer_id=customer_id,
        financial_stress_score=stress_score,
        recommended_action=recommended_action,
        key_signals=KeySignals(**current_state),
        recent_transactions=recent_transactions
    )

@app.get("/")
def read_root():
    return {"status": "API is running. Use /customer/{customer_id} to get data."}
