"""
Unit Tests for Pipelined Processor Module (CO5)
"""

import unittest
from bank_fraud_simulator.isa import parse_assembly, Opcode
from bank_fraud_simulator.memory import Memory
from bank_fraud_simulator.pipeline import PipelinedCPU, BranchPredictorMode, TwoBitBranchPredictor


class TestPipelinedProcessor(unittest.TestCase):
    def test_branch_predictor_state_transitions(self):
        bp = TwoBitBranchPredictor()
        pc = 0x0100

        # Initial state is 01 (Weakly Not Taken) -> predict False
        taken, _ = bp.predict(pc)
        self.assertFalse(taken)

        # Branch taken -> transitions to 10 (Weakly Taken)
        bp.update(pc, actual_taken=True, actual_target=0x0200)
        taken, target = bp.predict(pc)
        self.assertTrue(taken)
        self.assertEqual(target, 0x0200)

        # Branch taken again -> transitions to 11 (Strongly Taken)
        bp.update(pc, actual_taken=True, actual_target=0x0200)
        taken, _ = bp.predict(pc)
        self.assertTrue(taken)

        # Branch not taken -> transitions to 10 (Weakly Taken, still predicts Taken)
        bp.update(pc, actual_taken=False, actual_target=0x0200)
        taken, _ = bp.predict(pc)
        self.assertTrue(taken)

        # Branch not taken again -> transitions to 01 (Weakly Not Taken, now predicts Not Taken)
        bp.update(pc, actual_taken=False, actual_target=0x0200)
        taken, _ = bp.predict(pc)
        self.assertFalse(taken)

    def test_pipeline_forwarding_vs_stalls(self):
        asm_raw = """
        ADDI R1, R0, #10
        ADDI R3, R1, #20
        HALT
        """
        program = parse_assembly(asm_raw)

        # 1. With Forwarding ENABLED:
        mem_fwd = Memory()
        pipe_fwd = PipelinedCPU(memory=mem_fwd, enable_forwarding=True)
        pipe_fwd.run(program)
        self.assertEqual(pipe_fwd.get_register(1), 10)
        self.assertEqual(pipe_fwd.get_register(3), 30)
        self.assertGreater(pipe_fwd.forward_a_events, 0)

        # 2. With Forwarding DISABLED:
        mem_no_fwd = Memory()
        pipe_no_fwd = PipelinedCPU(memory=mem_no_fwd, enable_forwarding=False)
        pipe_no_fwd.run(program)
        self.assertEqual(pipe_no_fwd.get_register(1), 10)
        self.assertEqual(pipe_no_fwd.get_register(3), 30)
        self.assertGreater(pipe_no_fwd.stall_cycles, 0)
        self.assertLessEqual(pipe_fwd.cycle_count, pipe_no_fwd.cycle_count)


if __name__ == "__main__":
    unittest.main()

