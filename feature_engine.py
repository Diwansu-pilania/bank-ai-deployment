# feature_engine.py (Version 4 - Final Corrected Merge)
import pandas as pd
import numpy as np

print("--- Starting Feature Engineering Engine (v4 - Final Corrected Merge) ---")

# --- Load Raw Data ---
try:
    transactions_df = pd.read_csv('rich_transactions.csv', parse_dates=['timestamp'])
    balance_df = pd.read_csv('balance_snapshots.csv', parse_dates=['timestamp'])
    truth_df = pd.read_csv('stressed_customers_ground_truth.csv')
    customers_df = pd.read_csv('customers.csv')
    merchants_df = pd.read_csv('merchants.csv') # Load merchants data
    gnn_features_df = pd.read_csv('gnn_network_features.csv')
    print("All raw data files loaded successfully.")
except FileNotFoundError as e:
    print(f"FATAL ERROR: Missing data file - {e}. Please run all previous steps.")
    exit()

# --- THE FIX: Merge merchant category into transactions ---
transactions_df = pd.merge(transactions_df, merchants_df[['merchant_id', 'category']], on='merchant_id', how='left')
print("Merged merchant categories into transactions.")

# --- Initialize Feature DataFrame ---
features_df = customers_df.copy()
features_df['is_stressed'] = features_df['customer_id'].isin(truth_df['customer_id']).astype(int)

# --- Robust Feature Calculation Function ---
def calculate_and_merge_feature(main_df, feature_series, feature_name):
    feature_df = feature_series.reset_index(name=feature_name)
    merged_df = pd.merge(main_df, feature_df, on='customer_id', how='left')
    merged_df[feature_name] = merged_df[feature_name].fillna(0).astype(int)
    return merged_df

# --- Engineer All 7 Signals Robustly ---

# Signal 1: Late Salary Count
late_salaries = transactions_df[(transactions_df['merchant_id'] == 'SALARY') & (transactions_df['timestamp'].dt.day > 29)]
late_salary_counts = late_salaries.groupby('customer_id').size()
features_df = calculate_and_merge_feature(features_df, late_salary_counts, 'feature_late_salary_count')
print("Engineered Signal 1: Late Salary Count")

# Signal 2: Balance Decline Weeks
balance_df['balance_pct_change'] = balance_df.sort_values('timestamp').groupby('customer_id')['balance'].pct_change()
decline_weeks = balance_df[balance_df['balance_pct_change'] < -0.10]
decline_week_counts = decline_weeks.groupby('customer_id').size()
features_df = calculate_and_merge_feature(features_df, decline_week_counts, 'feature_decline_week_count')
print("Engineered Signal 2: Balance Decline Weeks")

# Signal 3: Lending App Transactions
lending_tx = transactions_df[transactions_df['merchant_id'] == 'LENDINGAPP01']
lending_counts = lending_tx.groupby('customer_id').size()
features_df = calculate_and_merge_feature(features_df, lending_counts, 'feature_lending_app_tx_count')
print("Engineered Signal 3: Lending App Transactions")

# Signal 4: Late Utility Payments
late_utilities = transactions_df[(transactions_df['merchant_id'] == 'UTILITY01') & (transactions_df['timestamp'].dt.day > 16)]
late_utility_counts = late_utilities.groupby('customer_id').size()
features_df = calculate_and_merge_feature(features_df, late_utility_counts, 'feature_late_utility_count')
print("Engineered Signal 4: Late Utility Payments")

# Signal 5: Discretionary Spending Ratio
# Now this will work because the 'category' column exists
total_spending = transactions_df[transactions_df['type'] == 'DEBIT'].groupby('customer_id')['amount'].sum()
discretionary_categories = ['Dining', 'Entertainment', 'Shopping', 'Travel']
discretionary_spending = transactions_df[transactions_df['category'].isin(discretionary_categories)].groupby('customer_id')['amount'].sum()
discretionary_ratio = (discretionary_spending / total_spending).fillna(0.5)
discretionary_ratio.name = 'feature_discretionary_spend_ratio'
features_df = features_df.merge(discretionary_ratio, on='customer_id', how='left')
features_df['feature_discretionary_spend_ratio'] = features_df['feature_discretionary_spend_ratio'].fillna(0.5)
print("Engineered Signal 5: Discretionary Spending Ratio")

# Signal 6: ATM Withdrawals
atm_tx = transactions_df[transactions_df['merchant_id'] == 'ATM01']
atm_counts = atm_tx.groupby('customer_id').size()
features_df = calculate_and_merge_feature(features_df, atm_counts, 'feature_atm_withdrawal_count')
print("Engineered Signal 6: ATM Withdrawals")

# Signal 7: Failed Auto-Debits
failed_debits = transactions_df[transactions_df['status'] == 'FAILED']
failed_debit_counts = failed_debits.groupby('customer_id').size()
features_df = calculate_and_merge_feature(features_df, failed_debit_counts, 'feature_failed_debit_count')
print("Engineered Signal 7: Failed Auto-Debits")

# --- Merge GNN Feature ---
features_df = features_df.merge(gnn_features_df, on='customer_id', how='left')
features_df['network_stress_feature'] = features_df['network_stress_feature'].fillna(0)
print("Merged GNN Network Feature")

# --- Finalize and Save ---
print("\n--- Feature Engineering Complete! ---")
features_df.to_csv('customer_features.csv', index=False)
print("Final dataset with all features saved to 'customer_features.csv'.")

# --- Sanity Check ---
print("\n--- Sanity Check: Feature Averages by Customer Group ---")
numeric_cols = features_df.select_dtypes(include=np.number).columns.tolist()
print(features_df.groupby('is_stressed')[numeric_cols].mean())
