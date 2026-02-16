# maintenance.py (Scheduled Feature Decay Script)
import json
import os

FEATURE_STORE_PATH = 'feature_store.json'
TEMP_FEATURE_STORE_PATH = 'feature_store.json.tmp'
DECAY_FACTOR = 0.5  # Har hafte features ko aadha kar do

print("--- Starting Weekly Feature Store Maintenance ---")

if not os.path.exists(FEATURE_STORE_PATH):
    print("Feature store not found. Nothing to do.")
    exit()

try:
    with open(FEATURE_STORE_PATH, 'r') as f:
        feature_store = json.load(f)
except Exception as e:
    print(f"Could not read feature store: {e}")
    exit()

print(f"Found {len(feature_store)} customers. Applying decay factor of {DECAY_FACTOR}...")

for customer_id, features in feature_store.items():
    # Sirf count waale features ko decay karo
    features['feature_late_salary_count'] *= DECAY_FACTOR
    features['feature_decline_week_count'] *= DECAY_FACTOR
    features['feature_lending_app_tx_count'] *= DECAY_FACTOR
    features['feature_late_utility_count'] *= DECAY_FACTOR
    features['feature_atm_withdrawal_count'] *= DECAY_FACTOR
    features['feature_failed_debit_count'] *= DECAY_FACTOR

    # Unko integer mein round kar do
    for key in features:
        if key.endswith('_count'):
            features[key] = int(features[key])

# Atomic save
with open(TEMP_FEATURE_STORE_PATH, 'w') as f:
    json.dump(feature_store, f, indent=2)
os.replace(TEMP_FEATURE_STORE_PATH, FEATURE_STORE_PATH)

print("--- Maintenance Complete. Feature store has been decayed. ---")
