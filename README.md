# 🏦 BankAI — Real-Time Financial Stress Detection & Smart Intervention System

> *Preventing financial crises before they happen.*

BankAI is an intelligent real-time banking assistant that continuously monitors customer transactions, detects early financial stress patterns, and automatically recommends the best intervention strategy using Machine Learning + Graph Intelligence + Reinforcement Learning.

---

## 🌍 Why This Matters

Banks usually detect financial distress **after default happens**.

BankAI changes the paradigm:

**From Reactive Banking → To Preventive Banking**

Instead of penalties, the system offers help:

* Gentle nudges
* Personalized offers
* Human assistance
* Risk prevention

---

## 🧠 Core Idea

Every transaction tells a story.

BankAI listens to that story in real time and answers:

> **"Is this customer heading toward financial trouble?"**
> **"What is the best action we should take now?"**

---

## 🏗️ System Architecture

```
Transactions → Kafka → Feature Engine → AI Models → API → Dashboard → Intervention
```

### Components

| Layer                     | Technology      | Purpose                      |
| ------------------------- | --------------- | ---------------------------- |
| Data Streaming            | Kafka           | Live transaction ingestion   |
| Processing Engine         | Python Consumer | Feature computation          |
| Prediction Model          | XGBoost         | Financial stress probability |
| Relationship Intelligence | GNN Features    | Social risk influence        |
| Decision Maker            | RL Agent (PPO)  | Best intervention            |
| Backend                   | FastAPI         | Exposes predictions          |
| Frontend                  | HTML + JS       | Real-time dashboard          |

---

## 🔄 Activity Flow (How It Works)

### 1️⃣ Live Transaction Simulation

`producer.py`

* Streams transactions from dataset
* Sends JSON messages to Kafka topic `financial_transactions`

---

### 2️⃣ Real-Time Feature Engine

`consumer.py`

For each transaction:

* Identify customer
* Update behavioral signals
* Merge network risk (GNN features)
* Save to `feature_store.json`

This acts as a **real-time behavioral database**

---

### 3️⃣ Financial Stress Prediction

Model: `financial_stress_predictor.pkl` (XGBoost)

Output:

```
Stress Score = 0.0 → 1.0
0.00 - 0.39 → Healthy
0.40 - 0.69 → Watchlist
0.70 - 1.00 → Critical
```

---

### 4️⃣ API Layer

`main.py` — FastAPI

Endpoint:

```
GET /customer/{customer_id}
```

Returns:

* Stress Score
* Risk Factors
* Transaction History

---

### 5️⃣ Interactive Dashboard

`static/index.html`

Modes:
🟢 Green → Safe
🟠 Yellow → Risk Building
🔴 Red → Immediate Attention

Live updates as transactions stream.

---

### 6️⃣ Intelligent Intervention Agent

`train_rl_agent.py`

Reinforcement Learning decides best action:

| Action | Meaning     |
| ------ | ----------- |
| 0      | Do Nothing  |
| 1      | SMS Nudge   |
| 2      | Email Offer |
| 3      | Human Call  |

Goal:
**Minimize long-term financial stress, not just immediate risk**

---

## 📊 Key Behavioral Signals Used

| Signal              | Meaning                    |
| ------------------- | -------------------------- |
| Late Salary         | Salary credited after 28th |
| Balance Decline     | Weekly drop >10%           |
| Lending App Usage   | Borrowing behavior         |
| Late Utility        | Bills paid after due date  |
| Discretionary Spend | Dining & lifestyle ratio   |
| ATM Withdrawals     | Liquidity stress           |
| Failed Debits       | Payment failures           |

---

## 🧪 How To Run (Demo Guide)

### Step 1 — Start Kafka

```
zookeeper-server-start.sh config/zookeeper.properties
kafka-server-start.sh config/server.properties
```

### Step 2 — Start Engine

```
python consumer.py
```

### Step 3 — Start API

```
uvicorn main:app --reload
```

### Step 4 — Open Dashboard

Open:

```
static/index.html
```

### Step 5 — Inject Live Data

```
python producer.py
```

🎯 Now watch customer stress evolve live!

---

## 🧠 AI Stack

* XGBoost → Predict financial stress
* Graph Features → Social risk propagation
* PPO Reinforcement Learning → Optimal intervention
* FastAPI → Low latency serving
* Kafka → Real-time ingestion

---

## 💡 Example Use Cases

* Prevent loan defaults
* Detect salary instability
* Identify over-borrowing early
* Offer proactive credit restructuring
* Improve customer trust

---

## 🏁 Future Scope

* WhatsApp bot integration
* Credit score enhancement
* Personalized financial coaching
* Fraud + stress combined detection

---

## 👨‍💻 Team Vision

We believe banking should **support customers, not punish them**.

BankAI turns transaction data into care, guidance, and timely help.

> *The best loan recovery is the one you never need.*

---

⭐ If you like this project — star the repo!
