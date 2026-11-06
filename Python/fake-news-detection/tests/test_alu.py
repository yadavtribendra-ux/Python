"""
Unit Tests for ALU and Logic Gate Modules (CO2)
"""

import unittest
from bank_fraud_simulator.alu import ALU, ALUStatusFlags
from bank_fraud_simulator.logic_gates import LogicGates, FraudBitmaskLogic


class TestALUAndLogic(unittest.TestCase):
    def test_logic_gates(self):
        self.assertEqual(LogicGates.gate_and(1, 1), 1)
        self.assertEqual(LogicGates.gate_and(1, 0), 0)
        self.assertEqual(LogicGates.gate_or(1, 0), 1)
        self.assertEqual(LogicGates.gate_or(0, 0), 0)
        self.assertEqual(LogicGates.gate_xor(1, 1), 0)
        self.assertEqual(LogicGates.gate_xor(1, 0), 1)
        self.assertEqual(LogicGates.gate_not(1), 0)
        self.assertEqual(LogicGates.gate_not(0), 1)

        # 2:1 Multiplexer
        self.assertEqual(LogicGates.mux_2to1(10, 20, sel=0), 10)
        self.assertEqual(LogicGates.mux_2to1(10, 20, sel=1), 20)

        # 1-bit Full Adder
        sum_bit, cout = LogicGates.full_adder_1bit(1, 1, 0)
        self.assertEqual((sum_bit, cout), (0, 1))

        sum_bit, cout = LogicGates.full_adder_1bit(1, 1, 1)
        self.assertEqual((sum_bit, cout), (1, 1))

    def test_alu_arithmetic(self):
        alu = ALU()

        # Addition
        res, flags = alu.execute("ADD", 50, 25)
        self.assertEqual(res, 75)
        self.assertFalse(flags.zero)
        self.assertFalse(flags.negative)

        # Subtraction yielding zero
        res, flags = alu.execute("SUB", 100, 100)
        self.assertEqual(res, 0)
        self.assertTrue(flags.zero)

        # Subtraction yielding negative
        res, flags = alu.execute("SUB", 50, 100)
        self.assertTrue(flags.negative)
        self.assertTrue(flags.less)

        # Absolute difference
        res, _ = alu.execute("ABS_DIFF", 30, 80)
        self.assertEqual(res, 50)

    def test_alu_bitwise_and_comparison(self):
        alu = ALU()

        # Bitwise AND
        res, _ = alu.execute("AND", 0b1100, 0b1010)
        self.assertEqual(res, 0b1000)

        # Bitwise OR
        res, _ = alu.execute("OR", 0b1100, 0b1010)
        self.assertEqual(res, 0b1110)

        # Greater than comparison
        res, flags = alu.execute("CMP_GT", 100, 50)
        self.assertEqual(res, 1)
        self.assertTrue(flags.greater)

        # Equal comparison
        res, flags = alu.execute("CMP_EQ", 42, 42)
        self.assertEqual(res, 1)
        self.assertTrue(flags.zero)

    def test_fraud_bitmask_logic(self):
        mask = 0
        # Set Large Amount flag
        mask = FraudBitmaskLogic.set_flag(mask, FraudBitmaskLogic.BIT_LARGE_AMOUNT, True)
        self.assertTrue(FraudBitmaskLogic.test_flag(mask, FraudBitmaskLogic.BIT_LARGE_AMOUNT))
        self.assertFalse(FraudBitmaskLogic.test_flag(mask, FraudBitmaskLogic.BIT_VELOCITY_SPIKE))

        # Set Velocity Spike flag
        mask = FraudBitmaskLogic.set_flag(mask, FraudBitmaskLogic.BIT_VELOCITY_SPIKE, True)
        decoded = FraudBitmaskLogic.decode_mask(mask)
        self.assertEqual(len(decoded), 2)

        # Risk score calculation
        risk = FraudBitmaskLogic.calculate_hardware_risk_score(mask)
        self.assertGreaterEqual(risk, 4)


if __name__ == "__main__":
    unittest.main()

