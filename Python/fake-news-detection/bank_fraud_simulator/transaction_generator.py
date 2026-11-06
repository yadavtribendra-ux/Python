"""
Transaction Stream Generator Module
===================================
Generates realistic financial transaction streams with synthetic normal
and anomalous banking fraud scenarios for architectural stress-testing.

Course Outcome Mapping:
- CO6: Real-world workload generation for performance evaluation and benchmark analysis.
"""

import random
from typing import List, Dict, Any


class TransactionGenerator:
    """Generates synthetic banking transactions with realistic feature distributions."""

    @staticmethod
    def generate_single_transaction(
        txn_id: int,
        scenario: str = "random",
        user_balance: float = 120000.0,
    ) -> Dict[str, Any]:
        """
        Creates a transaction dictionary with features needed for fraud processing:
        - amount: Transaction amount (NPR / Currency units)
        - balance: Current account balance
        - frequency: Transaction count in last 10 minutes
        - failed_pins: Recent failed PIN / authentication attempts
        - geo_speed: Velocity from previous transaction location (km/h)
        - mcc: Merchant Category Code (e.g. 5411 Grocery, 7995 Gambling)
        - new_device: Boolean indicating unrecognized hardware fingerprint
        - hour: Time of day (0-23)
        """
        scenarios = ["normal", "velocity_spike", "account_takeover", "impossible_travel", "large_cashout"]
        if scenario == "random":
            # 70% normal, 30% fraud distributions
            scenario = random.choices(
                scenarios, weights=[0.70, 0.10, 0.08, 0.06, 0.06], k=1
            )[0]

        if scenario == "normal":
            amount = round(random.uniform(200.0, 15000.0), 2)
            frequency = random.randint(1, 3)
            failed_pins = 0
            geo_speed = random.randint(0, 80)
            mcc = random.choice([5411, 5812, 5912, 4814, 5311])  # Grocery, Restaurant, Drugstore, Telecom
            new_device = False
            hour = random.randint(7, 22)
            expected_decision = "APPROVE"

        elif scenario == "velocity_spike":
            amount = round(random.uniform(5000.0, 25000.0), 2)
            frequency = random.randint(6, 15)  # Spike > 5
            failed_pins = random.choice([0, 1])
            geo_speed = random.randint(20, 120)
            mcc = random.choice([5411, 5732])
            new_device = random.choice([False, True])
            hour = random.randint(10, 20)
            expected_decision = "REVIEW"

        elif scenario == "account_takeover":
            amount = round(random.uniform(20000.0, 60000.0), 2)
            frequency = random.randint(2, 4)
            failed_pins = random.randint(3, 5)  # Repeated failures >= 3
            geo_speed = random.randint(50, 200)
            mcc = 6051  # Quasi-cash / Crypto / Money Transfer
            new_device = True  # New device
            hour = random.randint(1, 4)  # Anomalous off-hours
            expected_decision = "REJECT"

        elif scenario == "impossible_travel":
            amount = round(random.uniform(10000.0, 45000.0), 2)
            frequency = 2
            failed_pins = 0
            geo_speed = random.randint(900, 2500)  # Impossible physical speed > 800 km/h
            mcc = random.choice([5812, 7011])
            new_device = True
            hour = random.randint(0, 23)
            expected_decision = "REJECT"

        else:  # large_cashout
            amount = round(random.uniform(80000.0, 180000.0), 2)
            frequency = 2
            failed_pins = random.choice([0, 1])
            geo_speed = random.randint(10, 60)
            mcc = 6011  # ATM Cash withdrawal
            new_device = random.choice([False, True])
            hour = random.randint(9, 21)
            expected_decision = "REJECT" if amount > user_balance else "REVIEW"

        return {
            "id": txn_id,
            "scenario": scenario,
            "amount": amount,
            "balance": user_balance,
            "frequency": frequency,
            "failed_pins": failed_pins,
            "geo_speed": geo_speed,
            "mcc": mcc,
            "new_device": new_device,
            "hour": hour,
            "expected_decision": expected_decision,
        }

    @classmethod
    def generate_stream(cls, count: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
        """Generates a reproducible stream of banking transactions."""
        random.seed(seed)
        stream = []
        for i in range(1, count + 1):
            stream.append(cls.generate_single_transaction(txn_id=i))
        return stream
