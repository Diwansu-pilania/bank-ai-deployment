# train_rl_agent.py (Version 2.1 - Final Corrected Version)
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import random
import pickle

print("--- RL Intervention Agent with Dynamic Simulation Environment ---")

# --- 1. Load the Prediction Model ---
# The environment needs the trained XGBoost model to calculate the stress score, which is part of the reward.
try:
    with open('financial_stress_predictor.pkl', 'rb') as file:
        PREDICTOR_MODEL = pickle.load(file)
    FEATURE_NAMES = PREDICTOR_MODEL.get_booster().feature_names
    print("Successfully loaded the financial stress predictor model.")
except FileNotFoundError:
    print("FATAL: financial_stress_predictor.pkl not found. Please run train_final_model.py first.")
    exit()


# --- 2. Define the DYNAMIC Customer Environment ---

class DynamicFinancialCustomerEnv(gym.Env):
    """
    A simulated environment representing a financially stressed customer.
    The RL agent will interact with this environment to learn the best intervention policy.
    """

    def __init__(self):
        super(DynamicFinancialCustomerEnv, self).__init__()

        # --- Define Action and Observation Space ---
        self.action_space = spaces.Discrete(4)  # 0:None, 1:SMS, 2:Email, 3:Call
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(8,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        """Resets the environment to a new random customer state."""
        super().reset(seed=seed)
        # --- Initialize a new "customer" for a 90-day episode ---
        self.day = 0
        self.is_initially_stressed = random.choice([True, False])
        self.stress_level = 1.0 if self.is_initially_stressed else 0.1

        # Initialize the 8 features that define the state
        self.state = {
            'feature_late_salary_count': 0,
            'feature_decline_week_count': 0,
            'feature_lending_app_tx_count': 0,
            'feature_late_utility_count': 0,
            'feature_discretionary_spend_ratio': 0.5,
            'feature_atm_withdrawal_count': 0,
            'feature_failed_debit_count': 0,
            'network_stress_feature': random.uniform(0.1, 0.9) if self.is_initially_stressed else random.uniform(0.0,
                                                                                                                 0.4)
        }
        return self._get_obs(), {}

    def _get_obs(self):
        """Convert the state dictionary to a numpy array for the agent."""
        return np.array(list(self.state.values()), dtype=np.float32)

    def _get_current_stress_score(self):
        """Use the loaded XGBoost model to get the current stress score."""
        obs_df = pd.DataFrame([self.state], columns=FEATURE_NAMES)
        return PREDICTOR_MODEL.predict_proba(obs_df)[0, 1]

    def step(self, action):
        self.day += 1
        previous_score = self._get_current_stress_score()

        # --- Simulate Consequences of the Action ---
        action_effectiveness = 0
        if action == 1:
            action_effectiveness = 0.15
        elif action == 2:
            action_effectiveness = 0.25
        elif action == 3:
            action_effectiveness = 0.40

        self.stress_level -= (action_effectiveness * self.stress_level)
        if not self.is_initially_stressed and action > 0:
            self.stress_level += 0.1

        self.stress_level *= random.uniform(0.98, 1.01)
        self.stress_level = np.clip(self.stress_level, 0.0, 1.5)

        # --- Simulate New Transactions based on the NEW stress level ---
        if random.random() < self.stress_level * 0.1: self.state['feature_lending_app_tx_count'] += 1
        if random.random() < self.stress_level * 0.05: self.state['feature_failed_debit_count'] += 1
        if random.random() < self.stress_level * 0.2: self.state['feature_discretionary_spend_ratio'] *= 0.98

        # --- Calculate Reward ---
        new_score = self._get_current_stress_score()
        reward = previous_score - new_score
        if action > 0: reward -= 0.02

        done = self.day >= 90
        return self._get_obs(), reward, done, False, {}


# --- 2. Train the RL Agent ---
env = DynamicFinancialCustomerEnv()

model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_financial_tensorboard/")

print("\n--- Training Dynamic RL Agent... ---")
model.learn(total_timesteps=50000)
print("--- RL Training Complete ---")

# --- 3. Save the Trained Policy ---
model_filename = "intervention_agent_dynamic.zip"
model.save(model_filename)
print(f"\n--- Dynamic intervention agent policy saved to '{model_filename}' ---")

# --- 4. Test the Trained Agent ---
print("\n--- Testing Trained Agent ---")
obs, _ = env.reset()
for i in range(10):
    action, _states = model.predict(obs, deterministic=True)
    score = env._get_current_stress_score()
    actions_map = {0: "Do Nothing", 1: "Send SMS Nudge", 2: "Send Email Offer", 3: "Flag for Human Call"}

    # THE FIX: Use .item() to extract the number from the numpy array
    action_item = action.item()

    print(f"Day {env.day}: Stress Score={score:.2f} -> Agent's Action: {actions_map[action_item]}")

    obs, reward, done, _, info = env.step(action)
    if done:
        print("--- Episode Finished ---")
        break
