"""
Architectural Evaluation & Comparative Benchmark Engine
======================================================
Evaluates execution of repeated logical and arithmetic transaction rules across
distinct microarchitectural configurations to quantitatively measure speedup,
CPI, pipeline efficiency, and cache impact.

Course Outcome Mapping:
- CO6: Performance evaluation, quantitative metrics (CPI, MIPS, Speedup, AMAT),
  Amdahl's Law validation, and trade-off analysis.
"""

import time
from typing import List, Dict, Any, Tuple
from .isa import Instruction
from .memory import Memory
from .cache import Cache, ReplacementPolicy, WritePolicy
from .instruction_cycle import SingleCycleCPU
from .pipeline import PipelinedCPU, BranchPredictorMode
from .fraud_rules import BankFraudRules
from .logic_gates import FraudBitmaskLogic


class ArchitectureBenchmark:
    """
    Harness that runs workloads across 5 distinct architectural configurations:
      1. SingleCycle_NoCache
      2. SingleCycle_WithCache
      3. Pipeline_NoForwarding_StaticBranch
      4. Pipeline_Forwarding_2BitBranch
      5. FullOptimized_Pipeline_Forwarding_BranchPredictor_DualCache
    """

    @classmethod
    def run_single_transaction_all_configs(
        cls,
        txn: Dict[str, Any],
        program: List[Instruction],
        cache_size_bytes: int = 512,
        associativity: int = 2,
    ) -> Dict[str, Any]:
        """
        Executes a single transaction on all 5 architectures and returns detailed metrics.
        """
        results = {}

        # ---------------- CONFIG 1: Single Cycle (No Cache) ----------------
        mem1 = Memory()
        mem1.load_transaction_buffer(txn)
        cpu1 = SingleCycleCPU(memory=mem1, cache=None)
        cpu1.run(program)
        c1_insts = cpu1.instructions_executed
        # In un-cached memory: Instruction fetch = 20 cycles, Data access = 20 cycles, ALU = 1 cycle
        c1_cycles = cpu1.cycles * 5  # Realistic multi-cycle / un-cached delay model

        # ---------------- CONFIG 2: Single Cycle + L1 Cache ----------------
        mem2 = Memory()
        mem2.load_transaction_buffer(txn)
        cache2 = Cache("L1-Unified", total_size_bytes=cache_size_bytes, associativity=associativity)
        cpu2 = SingleCycleCPU(memory=mem2, cache=cache2)
        cpu2.run(program)
        c2_insts = cpu2.instructions_executed
        c2_cycles = int(cpu2.cycles * cache2.amat)

        # ---------------- CONFIG 3: Pipelined (No Forwarding, Stalls, Static Branch) ----------------
        mem3 = Memory()
        mem3.load_transaction_buffer(txn)
        pipe3 = PipelinedCPU(
            memory=mem3,
            i_cache=None,
            d_cache=None,
            enable_forwarding=False,
            branch_predictor_mode=BranchPredictorMode.ALWAYS_NOT_TAKEN,
        )
        pipe3.run(program)
        c3_cycles = pipe3.cycle_count
        c3_insts = pipe3.instructions_retired

        # ---------------- CONFIG 4: Pipelined + Forwarding + 2-Bit Branch Predictor (No Cache) ----------------
        mem4 = Memory()
        mem4.load_transaction_buffer(txn)
        pipe4 = PipelinedCPU(
            memory=mem4,
            i_cache=None,
            d_cache=None,
            enable_forwarding=True,
            branch_predictor_mode=BranchPredictorMode.DYNAMIC_2BIT,
        )
        pipe4.run(program)
        c4_cycles = pipe4.cycle_count
        c4_insts = pipe4.instructions_retired

        # ---------------- CONFIG 5: Fully Optimized (Pipeline + Forwarding + Predictor + Dual Cache) ----------------
        mem5 = Memory()
        mem5.load_transaction_buffer(txn)
        i_cache5 = Cache("L1-ICache", total_size_bytes=cache_size_bytes, associativity=associativity)
        d_cache5 = Cache("L1-DCache", total_size_bytes=cache_size_bytes, associativity=associativity)
        pipe5 = PipelinedCPU(
            memory=mem5,
            i_cache=i_cache5,
            d_cache=d_cache5,
            enable_forwarding=True,
            branch_predictor_mode=BranchPredictorMode.DYNAMIC_2BIT,
        )
        pipe5.run(program)
        c5_cycles = pipe5.cycle_count
        c5_insts = pipe5.instructions_retired

        # Extract transaction fraud outcome from memory
        risk_score = mem5.read_word(Memory.DECISION_ADDR + 0)
        fraud_mask = mem5.read_word(Memory.DECISION_ADDR + 4)
        decision_code = mem5.read_word(Memory.DECISION_ADDR + 8)
        decision_map = {1: "APPROVE", 2: "REVIEW", 3: "REJECT"}
        decision = decision_map.get(decision_code, "UNKNOWN")

        baseline_cycles = max(1, c1_cycles)

        configs_data = [
            {
                "Config": "1. Single-Cycle (No Cache)",
                "Pipelined": False,
                "Forwarding": False,
                "Branch Predictor": "None",
                "Cache": "None",
                "Cycles": c1_cycles,
                "Instructions": c1_insts,
                "CPI": round(c1_cycles / max(1, c1_insts), 2),
                "Speedup": 1.0,
            },
            {
                "Config": "2. Single-Cycle + Cache",
                "Pipelined": False,
                "Forwarding": False,
                "Branch Predictor": "None",
                "Cache": f"{cache_size_bytes}B {associativity}-Way",
                "Cycles": c2_cycles,
                "Instructions": c2_insts,
                "CPI": round(c2_cycles / max(1, c2_insts), 2),
                "Speedup": round(baseline_cycles / max(1, c2_cycles), 2),
            },
            {
                "Config": "3. Pipeline (No Forwarding)",
                "Pipelined": True,
                "Forwarding": False,
                "Branch Predictor": "Static Not-Taken",
                "Cache": "None",
                "Cycles": c3_cycles,
                "Instructions": c3_insts,
                "CPI": round(pipe3.cpi, 2),
                "Speedup": round(baseline_cycles / max(1, c3_cycles), 2),
            },
            {
                "Config": "4. Pipeline + Forwarding + 2-Bit",
                "Pipelined": True,
                "Forwarding": True,
                "Branch Predictor": "Dynamic 2-Bit",
                "Cache": "None",
                "Cycles": c4_cycles,
                "Instructions": c4_insts,
                "CPI": round(pipe4.cpi, 2),
                "Speedup": round(baseline_cycles / max(1, c4_cycles), 2),
            },
            {
                "Config": "5. Full Optimized (Pipe+Fwd+Cache)",
                "Pipelined": True,
                "Forwarding": True,
                "Branch Predictor": "Dynamic 2-Bit",
                "Cache": f"L1 I/D {cache_size_bytes}B",
                "Cycles": c5_cycles,
                "Instructions": c5_insts,
                "CPI": round(pipe5.cpi, 2),
                "Speedup": round(baseline_cycles / max(1, c5_cycles), 2),
            },
        ]

        return {
            "txn_id": txn.get("id", 1),
            "amount": txn.get("amount", 0),
            "risk_score": risk_score,
            "fraud_mask": fraud_mask,
            "triggered_rules": FraudBitmaskLogic.decode_mask(fraud_mask),
            "decision": decision,
            "configs": configs_data,
            "pipeline_snapshots": pipe5.snapshots,
            "gantt_records": pipe5.gantt_records,
            "pipe3_metrics": pipe3.get_metrics(),
            "pipe4_metrics": pipe4.get_metrics(),
            "pipe5_metrics": pipe5.get_metrics(),
            "i_cache_summary": i_cache5.get_summary(),
            "d_cache_summary": d_cache5.get_summary(),
        }

    @classmethod
    def run_batch_benchmark(
        cls,
        txns: List[Dict[str, Any]],
        program: List[Instruction],
        cache_size_bytes: int = 512,
        associativity: int = 2,
    ) -> Dict[str, Any]:
        """
        Runs a batch of transactions repeatedly through the simulator to measure
        temporal locality, steady-state pipeline performance, and cache hit saturation.
        """
        start_time = time.time()
        total_txns = len(txns)

        # Persistent hardware caches across the transaction batch to demonstrate locality
        i_cache = Cache("L1-ICache", total_size_bytes=cache_size_bytes, associativity=associativity)
        d_cache = Cache("L1-DCache", total_size_bytes=cache_size_bytes, associativity=associativity)
        mem = Memory()

        pipe = PipelinedCPU(
            memory=mem,
            i_cache=i_cache,
            d_cache=d_cache,
            enable_forwarding=True,
            branch_predictor_mode=BranchPredictorMode.DYNAMIC_2BIT,
        )

        decisions = {"APPROVE": 0, "REVIEW": 0, "REJECT": 0}
        total_cycles = 0
        total_instructions = 0

        for txn in txns:
            mem.load_transaction_buffer(txn)
            pipe.pc = 0
            pipe.halted = False
            # Clear pipeline registers for next transaction but keep branch predictor table and cache!
            pipe.if_id.valid = False
            pipe.id_ex.valid = False
            pipe.ex_mem.valid = False
            pipe.mem_wb.valid = False

            cycles = pipe.run(program, max_cycles=500)
            total_cycles += cycles
            total_instructions += pipe.instructions_retired

            decision_code = mem.read_word(Memory.DECISION_ADDR + 8)
            dec_str = {1: "APPROVE", 2: "REVIEW", 3: "REJECT"}.get(decision_code, "UNKNOWN")
            decisions[dec_str] = decisions.get(dec_str, 0) + 1

        elapsed_sec = time.time() - start_time
        avg_cpi = (total_cycles / total_instructions) if total_instructions > 0 else 1.0

        # Theoretical single-cycle un-cached baseline cycles:
        baseline_cycles = total_instructions * 5

        return {
            "total_transactions": total_txns,
            "total_cycles": total_cycles,
            "total_instructions": total_instructions,
            "average_cpi": round(avg_cpi, 3),
            "overall_speedup": round(baseline_cycles / max(1, total_cycles), 2),
            "decisions": decisions,
            "i_cache_hit_rate": round(i_cache.hit_rate * 100, 2),
            "d_cache_hit_rate": round(d_cache.hit_rate * 100, 2),
            "branch_predictor_accuracy": round(pipe.branch_predictor.accuracy * 100, 2),
            "elapsed_seconds": round(elapsed_sec, 4),
            "transactions_per_second": round(total_txns / max(0.0001, elapsed_sec), 1),
            "i_cache_summary": i_cache.get_summary(),
            "d_cache_summary": d_cache.get_summary(),
        }
