import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

# --- Configuration ---
NUM_CUSTOMERS = 500
NUM_MERCHANTS = 20
TRANSACTIONS_PER_CUSTOMER_PER_DAY = 1
SIMULATION_DAYS = 365
STRESS_FACTOR = 0.2  # 20% of customers will be financially stressed

# Initialize Faker for generating realistic data
fake = Faker()

print("Starting synthetic data generation...")

# --- 1. Generate Customers ---
customers = [{'customer_id': f'C{i:04d}', 'name': fake.name()} for i in range(NUM_CUSTOMERS)]
customers_df = pd.DataFrame(customers)
print(f"Generated {len(customers_df)} customers.")

# --- 2. Generate Merchants ---
merchant_categories = ['Groceries', 'Dining', 'Entertainment', 'Transport', 'Shopping', 'Healthcare']
merchants = []
for i in range(NUM_MERCHANTS):
    merchants.append({
        'merchant_id': f'M{i:04d}',
        'name': fake.company(),
        'category': random.choice(merchant_categories)
    })
# Add special merchants crucial for feature engineering
merchants.append({'merchant_id': 'SALARY', 'name': 'EmployerCorp', 'category': 'Income'})
merchants.append({'merchant_id': 'LENDINGAPP01', 'name': 'QuickCash Loans', 'category': 'LendingApp'})
merchants.append({'merchant_id': 'UTILITY01', 'name': 'City Power & Water', 'category': 'Utilities'})
merchants_df = pd.DataFrame(merchants)
print(f"Generated {len(merchants_df)} merchants.")

# --- 3. Simulate Financial Stress ---
# Select a subset of customers to be "stressed"
stressed_customer_ids = random.sample(list(customers_df['customer_id']), int(NUM_CUSTOMERS * STRESS_FACTOR))
stressed_customers_df = pd.DataFrame(stressed_customer_ids, columns=['customer_id'])
print(f"Simulating financial stress for {len(stressed_customers_df)} customers.")

# --- 4. Generate Transactions ---
transactions = []
start_date = datetime.now() - timedelta(days=SIMULATION_DAYS)

for day in range(SIMULATION_DAYS):
    current_date = start_date + timedelta(days=day)

    for customer in customers:
        customer_id = customer['customer_id']
        is_stressed = customer_id in stressed_customer_ids

        # --- Salary Transaction ---
        # Normal salary day is around the 28th
        salary_day = 28
        if is_stressed and random.random() < 0.4:  # 40% chance of late salary for stressed customers
            salary_day += random.randint(3, 10)  # 3 to 10 days late

        if current_date.day == salary_day:
            transactions.append({
                'timestamp': current_date,
                'customer_id': customer_id,
                'merchant_id': 'SALARY',
                'amount': round(random.uniform(2000, 5000), 2),
                'type': 'CREDIT'
            })

        # --- Regular & Stressed Transactions ---
        num_transactions = random.randint(1, TRANSACTIONS_PER_CUSTOMER_PER_DAY + 1)
        for _ in range(num_transactions):
            merchant = merchants_df.sample(1).iloc[0]

            # Stressed customers have a chance to transact with lending apps
            if is_stressed and random.random() < 0.1:  # 10% chance per day
                merchant = merchants_df[merchants_df['category'] == 'LendingApp'].sample(1).iloc[0]

            transactions.append({
                'timestamp': current_date + timedelta(hours=random.randint(8, 22)),
                'customer_id': customer_id,
                'merchant_id': merchant['merchant_id'],
                'amount': round(random.uniform(5, 200), 2),
                'type': 'DEBIT'
            })

transactions_df = pd.DataFrame(transactions)
print(f"Generated {len(transactions_df)} transactions.")

# --- 5. Generate Relationships ---
relationships = []
for i in range(NUM_CUSTOMERS * 20):  # Generate a good number of connections
    c1, c2 = random.sample(list(customers_df['customer_id']), 2)
    # Avoid duplicate relationships
    if not any(d['customer_id_1'] == c2 and d['customer_id_2'] == c1 for d in relationships):
        relationships.append({
            'customer_id_1': c1,
            'customer_id_2': c2,
            'relationship_type': random.choice(['Social', 'Familial', 'Co-worker'])
        })
relationships_df = pd.DataFrame(relationships)
print(f"Generated {len(relationships_df)} customer relationships.")

# --- 6. Save to CSV Files ---
customers_df.to_csv('customers.csv', index=False)
merchants_df.to_csv('merchants.csv', index=False)
transactions_df.to_csv('transactions.csv', index=False)
relationships_df.to_csv('relationships.csv', index=False)
stressed_customers_df.to_csv('stressed_customers_ground_truth.csv', index=False)

print("\n--- Data Generation Complete! ---")
print("The following files have been created in your project folder:")
print("1. customers.csv")
print("2. merchants.csv")
print("3. transactions.csv")
print("4. relationships.csv")
print("5. stressed_customers_ground_truth.csv")

