"""
Unit Tests for Fraud Rules and End-to-End Simulation
"""

import unittest
from bank_fraud_simulator.fraud_rules import BankFraudRules
from bank_fraud_simulator.transaction_generator import TransactionGenerator
from bank_fraud_simulator.evaluator import ArchitectureBenchmark


class TestFraudRulesAndEndToEnd(unittest.TestCase):
    def test_rule_compilation(self):
        program = BankFraudRules.compile_rules()
        self.assertGreater(len(program), 15)
        for inst in program:
            word = inst.encode()
            self.assertGreaterEqual(word, 0)
            self.assertLessEqual(word, 0xFFFFFFFF)

    def test_normal_transaction_approval(self):
        program = BankFraudRules.compile_rules()
        normal_txn = {
            "id": 101,
            "amount": 2500.0,
            "balance": 50000.0,
            "frequency": 1,
            "failed_pins": 0,
            "geo_speed": 30,
            "mcc": 5411,
            "new_device": False,
            "hour": 15,
        }
        res = ArchitectureBenchmark.run_single_transaction_all_configs(txn=normal_txn, program=program)
        self.assertEqual(res["decision"], "APPROVE")
        self.assertLess(res["risk_score"], 4)
        self.assertEqual(res["fraud_mask"], 0)

    def test_velocity_spike_rejection_or_review(self):
        program = BankFraudRules.compile_rules(rapid_limit=5)
        velocity_txn = {
            "id": 102,
            "amount": 10000.0,
            "balance": 80000.0,
            "frequency": 12,  # Spike > 5
            "failed_pins": 0,
            "geo_speed": 40,
            "mcc": 5411,
            "new_device": False,
            "hour": 14,
        }
        res = ArchitectureBenchmark.run_single_transaction_all_configs(txn=velocity_txn, program=program)
        self.assertTrue(bool(res["fraud_mask"] & (1 << 1)))
        self.assertGreaterEqual(res["risk_score"], 2)

    def test_geo_impossible_speed(self):
        program = BankFraudRules.compile_rules(speed_limit=800)
        geo_txn = {
            "id": 103,
            "amount": 5000.0,
            "balance": 100000.0,
            "frequency": 1,
            "failed_pins": 0,
            "geo_speed": 1200,  # 1200 km/h > 800 km/h
            "mcc": 5411,
            "new_device": True,
            "hour": 12,
        }
        res = ArchitectureBenchmark.run_single_transaction_all_configs(txn=geo_txn, program=program)
        self.assertTrue(bool(res["fraud_mask"] & (1 << 2)))
        self.assertGreaterEqual(res["risk_score"], 5)
        self.assertIn(res["decision"], ("REVIEW", "REJECT"))


if __name__ == "__main__":
    unittest.main()

