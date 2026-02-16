# create_training_snapshots.py (Version 3 - Definitive, Complete & Correct)
import pandas as pd
import numpy as np

print("--- Starting Definitive Time-Aware Snapshot Generation (v3) ---")

# Load Raw Data
try:
    transactions_df = pd.read_csv('rich_transactions.csv', parse_dates=['timestamp'])
    merchants_df = pd.read_csv('merchants.csv')
    truth_df = pd.read_csv('stressed_customers_ground_truth.csv')
    gnn_features_df = pd.read_csv('gnn_network_features.csv')
    customers_df = pd.read_csv('customers.csv')
except FileNotFoundError as e:
    print(f"FATAL ERROR: Missing data file - {e}. Please run generate_rich_data.py first.")
    exit()

transactions_df = pd.merge(transactions_df, merchants_df[['merchant_id', 'category']], on='merchant_id', how='left')

# Iterate Through Time
all_snapshots = []
simulation_days = (transactions_df['timestamp'].max() - transactions_df['timestamp'].min()).days

for day in range(30, simulation_days + 1, 30):  # Create a snapshot every 30 days
    current_date = transactions_df['timestamp'].min() + pd.Timedelta(days=day)
    historical_transactions = transactions_df[transactions_df['timestamp'] <= current_date]

    if historical_transactions.empty: continue
    print(f"Processing snapshot for date: {current_date.date()}")

    features_df = customers_df.copy()
    features_df['snapshot_date'] = current_date


    def get_counts(df, col_name):
        counts = df.groupby('customer_id').size()
        return features_df['customer_id'].map(counts).fillna(0)


    # Calculate all 7 features based on data *up to this point in time*
    features_df['feature_late_salary_count'] = get_counts(historical_transactions[
                                                              (historical_transactions['merchant_id'] == 'SALARY') & (
                                                                          historical_transactions[
                                                                              'timestamp'].dt.day > 28)],
                                                          'feature_late_salary_count')
    features_df['feature_lending_app_tx_count'] = get_counts(
        historical_transactions[historical_transactions['merchant_id'] == 'LENDINGAPP01'],
        'feature_lending_app_tx_count')
    features_df['feature_late_utility_count'] = get_counts(historical_transactions[(historical_transactions[
                                                                                        'merchant_id'] == 'UTILITY01') & (
                                                                                               historical_transactions[
                                                                                                   'timestamp'].dt.day > 15)],
                                                           'feature_late_utility_count')
    features_df['feature_atm_withdrawal_count'] = get_counts(
        historical_transactions[historical_transactions['merchant_id'] == 'ATM01'], 'feature_atm_withdrawal_count')
    features_df['feature_failed_debit_count'] = get_counts(
        historical_transactions[historical_transactions['status'] == 'FAILED'], 'feature_failed_debit_count')

    # More complex features
    debit_tx = historical_transactions[historical_transactions['type'] == 'DEBIT']
    total_spending = debit_tx.groupby('customer_id')['amount'].sum()
    discretionary_spending = \
    debit_tx[debit_tx['category'].isin(['Dining', 'Entertainment', 'Shopping', 'Travel'])].groupby('customer_id')[
        'amount'].sum()
    discretionary_ratio = (discretionary_spending / total_spending).fillna(0.5)
    features_df['feature_discretionary_spend_ratio'] = features_df['customer_id'].map(discretionary_ratio).fillna(0.5)

    # Simplified balance decline
    weekly_net = historical_transactions.groupby(['customer_id', pd.Grouper(key='timestamp', freq='W-MON')])[
        'amount'].sum().reset_index()
    weekly_net['net_change'] = weekly_net.groupby('customer_id')['amount'].diff().fillna(0)
    decline_weeks = weekly_net[weekly_net['net_change'] < -500]
    features_df['feature_decline_week_count'] = features_df['customer_id'].map(
        decline_weeks.groupby('customer_id').size()).fillna(0)

    all_snapshots.append(features_df)

# Finalize and Save
training_data_df = pd.concat(all_snapshots, ignore_index=True)
training_data_df = pd.merge(training_data_df, gnn_features_df, on='customer_id', how='left')
training_data_df['is_stressed'] = training_data_df['customer_id'].isin(truth_df['customer_id']).astype(int)
training_data_df = training_data_df.fillna(0)
training_data_df.to_csv('final_training_data.csv', index=False)
print(f"\n--- Definitive training data created with {len(training_data_df)} snapshots. ---")
