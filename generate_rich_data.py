# generate_rich_data.py (Version 7 - Definitive Continuous Stress Spectrum)
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

print("--- Starting Data Generation (v7 - Continuous Stress Spectrum) ---")
NUM_CUSTOMERS = 1000
SIMULATION_DAYS = 365
START_DATE = datetime.now() - timedelta(days=SIMULATION_DAYS)
fake = Faker()

# Customers & Merchants
customers = [{'customer_id': f'C{i:04d}'} for i in range(NUM_CUSTOMERS)]
customers_df = pd.DataFrame(customers)
merchant_categories = {'discretionary': ['Dining', 'Entertainment', 'Shopping', 'Travel'],
                       'essential': ['Groceries', 'Transport', 'Healthcare']}
special_merchants = [{'merchant_id': 'SALARY', 'name': 'EmployerCorp', 'category': 'Income'},
                     {'merchant_id': 'LENDINGAPP01', 'name': 'QuickCash Loans', 'category': 'LendingApp'},
                     {'merchant_id': 'UTILITY01', 'name': 'City Power', 'category': 'Utilities'},
                     {'merchant_id': 'ATM01', 'name': 'Global ATM Network', 'category': 'ATM'},
                     {'merchant_id': 'LOAN01', 'name': 'Auto Loan Finance', 'category': 'Loan'}]
merchants = special_merchants.copy()
for i in range(30):
    cat_type = 'discretionary' if random.random() > 0.3 else 'essential'
    merchants.append(
        {'merchant_id': f'M{i:04d}', 'name': fake.company(), 'category': random.choice(merchant_categories[cat_type])})
merchants_df = pd.DataFrame(merchants)

# Continuous Stress Level for each customer
customer_stress_levels = {cid: np.random.beta(a=2, b=3) for cid in customers_df['customer_id']}
STRESS_THRESHOLD = 0.6
stressed_customer_ids = [cid for cid, level in customer_stress_levels.items() if level > STRESS_THRESHOLD]
stressed_customers_df = pd.DataFrame(stressed_customer_ids, columns=['customer_id'])

# Generate Transactions
transactions = []
current_balances = {cid: random.uniform(500, 10000) for cid in customers_df['customer_id']}
for day in range(SIMULATION_DAYS):
    current_date = START_DATE + timedelta(days=day)
    for customer in customers:
        cid = customer['customer_id']
        stress = customer_stress_levels[cid]

        # Salary (can be late)
        if current_date.day == 28:
            salary_date = current_date + timedelta(
                days=random.randint(1, 5)) if random.random() < stress * 0.1 else current_date
            transactions.append({'timestamp': salary_date, 'customer_id': cid, 'merchant_id': 'SALARY',
                                 'amount': random.uniform(2000, 5000), 'type': 'CREDIT', 'status': 'COMPLETED'})

        # Utility (can be late)
        if current_date.day == 15 and random.random() < stress * 0.2:
            transactions.append({'timestamp': current_date + timedelta(days=random.randint(1, 7)), 'customer_id': cid,
                                 'merchant_id': 'UTILITY01', 'amount': random.uniform(50, 200), 'type': 'DEBIT',
                                 'status': 'COMPLETED'})

        # Failed Debit
        if current_date.day == 5 and random.random() < stress * 0.3:
            loan_amount = random.uniform(300, 800)
            status = 'FAILED' if current_balances[cid] < loan_amount else 'COMPLETED'
            transactions.append(
                {'timestamp': current_date, 'customer_id': cid, 'merchant_id': 'LOAN01', 'amount': loan_amount,
                 'type': 'DEBIT', 'status': status})
            if status == 'COMPLETED': current_balances[cid] -= loan_amount

        # Lending App & ATM
        if random.random() < stress * 0.15:
            transactions.append({'timestamp': current_date, 'customer_id': cid, 'merchant_id': 'LENDINGAPP01',
                                 'amount': random.uniform(50, 300), 'type': 'DEBIT', 'status': 'COMPLETED'})
        if random.random() < stress * 0.05 + 0.02:  # Everyone uses ATMs sometimes
            transactions.append({'timestamp': current_date, 'customer_id': cid, 'merchant_id': 'ATM01',
                                 'amount': random.uniform(20, 500), 'type': 'DEBIT', 'status': 'COMPLETED'})

        # Regular Daily Transactions
        for _ in range(random.randint(0, 5)):
            is_reducing = random.random() < stress * 0.5
            merchant_cat_type = 'essential' if is_reducing else random.choice(
                ['essential', 'discretionary', 'discretionary'])
            if not merchants_df[merchants_df['category'].isin(merchant_categories.get(merchant_cat_type, []))].empty:
                merchant = \
                merchants_df[merchants_df['category'].isin(merchant_categories[merchant_cat_type])].sample(1).iloc[0]
                if current_balances[cid] > 150:
                    tx = {'timestamp': current_date, 'customer_id': cid, 'merchant_id': merchant['merchant_id'],
                          'amount': random.uniform(10, 150), 'type': 'DEBIT', 'status': 'COMPLETED'}
                    transactions.append(tx)
                    current_balances[cid] -= tx['amount']

# Save to CSV
transactions_df = pd.DataFrame(transactions).sort_values('timestamp').reset_index(drop=True)
transactions_df.to_csv('rich_transactions.csv', index=False)
stressed_customers_df.to_csv('stressed_customers_ground_truth.csv', index=False)
customers_df.to_csv('customers.csv', index=False)
merchants_df.to_csv('merchants.csv', index=False)
print(f"Generated {len(transactions_df)} transactions.")
print("--- Definitive Data Generation Complete! ---")

