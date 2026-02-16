# maintenance.py (Version 3 - Final, Render-Ready, Single Service)
import json
import os
import time

print("--- Maintenance Job Starting ---")

# --- Config (Simple Paths for Single Service) ---
FEATURE_STORE_PATH = 'feature_store.json'
TEMP_FEATURE_STORE_PATH = 'feature_store.json.tmp'
DECAY_FACTOR = 0.9 # Each run, features will be reduced to 90% of their value

# --- State Management (Atomic save) ---
def load_feature_store():
    if os.path.exists(FEATURE_STORE_PATH):
        try:
            with open(FEATURE_STORE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("WARNING: Feature store was corrupted or not found. Cannot run maintenance.")
            return None
    print("Feature store not found. Nothing to do.")
    return None

def save_feature_store_to_disk(store):
    try:
        with open(TEMP_FEATURE_STORE_PATH, 'w') as f:
            json.dump(store, f, indent=2)
        os.replace(TEMP_FEATURE_STORE_PATH, FEATURE_STORE_PATH)
    except Exception as e:
        print(f"ERROR saving feature store: {e}")

# --- Main Logic ---
if __name__ == "__main__":
    feature_store = load_feature_store()

    if feature_store:
        print(f"Loaded feature store with {len(feature_store)} customers.")
        decayed_count = 0
        for customer_id, state in feature_store.items():
            # Decay only the count-based features
            state['feature_late_salary_count'] = int(state.get('feature_late_salary_count', 0) * DECAY_FACTOR)
            state['feature_decline_week_count'] = int(state.get('feature_decline_week_count', 0) * DECAY_FACTOR)
            state['feature_lending_app_tx_count'] = int(state.get('feature_lending_app_tx_count', 0) * DECAY_FACTOR)
            state['feature_late_utility_count'] = int(state.get('feature_late_utility_count', 0) * DECAY_FACTOR)
            state['feature_atm_withdrawal_count'] = int(state.get('feature_atm_withdrawal_count', 0) * DECAY_FACTOR)
            state['feature_failed_debit_count'] = int(state.get('feature_failed_debit_count', 0) * DECAY_FACTOR)
            decayed_count += 1
        
        print(f"Applied decay factor of {DECAY_FACTOR} to {decayed_count} customers.")
        save_feature_store_to_disk(feature_store)
        print("Successfully saved the decayed feature store.")
    
    print("--- Maintenance Job Finished ---")
