"""
Command Line Interface (CLI) for Bank Fraud Architecture Simulator
==================================================================
Runs cycle-by-cycle execution, hazard tracking, and batch benchmarks directly
from the terminal with ANSI/ASCII formatted tables.
"""

import sys
import argparse
import json
from bank_fraud_simulator.fraud_rules import BankFraudRules
from bank_fraud_simulator.transaction_generator import TransactionGenerator
from bank_fraud_simulator.evaluator import ArchitectureBenchmark
from bank_fraud_simulator.pedagogy import AcademicMapping


def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║       BANK FRAUD-RULE PROCESSING ARCHITECTURE SIMULATOR               ║
    ║   Evaluating Repeated Logical & Arithmetic Rules in Hardware Datapaths║
    ║     Logic • ALU • Instruction Cycle • 5-Stage Pipeline • L1 Cache     ║
    ║                  CT + RWE Framework | CO1–CO6                         ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_single(scenario: str = "velocity_spike"):
    print_banner()
    print(f"[*] Running single transaction evaluation with scenario: '{scenario}'")
    program = BankFraudRules.compile_rules()
    txn = TransactionGenerator.generate_single_transaction(txn_id=1, scenario=scenario)

    print("\n[+] Transaction Input Parameters:")
    for k, v in txn.items():
        print(f"    - {k:<18}: {v}")

    result = ArchitectureBenchmark.run_single_transaction_all_configs(txn=txn, program=program)

    print("\n[+] Hardware Decision & Registers:")
    print(f"    - Decision           : {result['decision']}")
    print(f"    - Hardware Risk Score: {result['risk_score']} / 10")
    print(f"    - FRAUD_MASK (R9)    : 0x{result['fraud_mask']:08X}")
    print("    - Asserted Rules     :")
    for rule in result["triggered_rules"]:
        print(f"      * {rule}")

    print("\n[+] Comparative Architectural Performance:")
    print(f"    {'Configuration':<38} | {'Cycles':<8} | {'CPI':<6} | {'Speedup':<8}")
    print("    " + "-" * 68)
    for cfg in result["configs"]:
        print(f"    {cfg['Config']:<38} | {cfg['Cycles']:<8} | {cfg['CPI']:<6.2f} | {cfg['Speedup']:<6.2f}x")

    print("\n[+] 5-Stage Pipeline Metrics:")
    p = result["pipe5_metrics"]
    for k, v in p.items():
        print(f"    - {k:<30}: {v}")

    print("\n[+] L1 Cache Subsystem Performance:")
    ic = result["i_cache_summary"]
    dc = result["d_cache_summary"]
    print(f"    - I-Cache Hit Rate   : {ic['Hit Rate (%)']}% (AMAT: {ic['AMAT (Cycles)']} cycles)")
    print(f"    - D-Cache Hit Rate   : {dc['Hit Rate (%)']}% (AMAT: {dc['AMAT (Cycles)']} cycles)")


def run_benchmark(batch_size: int = 50):
    print_banner()
    print(f"[*] Executing Batch Stress-Test with {batch_size} banking transactions...")
    program = BankFraudRules.compile_rules()
    stream = TransactionGenerator.generate_stream(count=batch_size, seed=42)

    res = ArchitectureBenchmark.run_batch_benchmark(txns=stream, program=program)

    print("\n[+] Benchmark Results Summary:")
    print(f"    - Total Transactions        : {res['total_transactions']}")
    print(f"    - Total Retired Instructions: {res['total_instructions']:,}")
    print(f"    - Total Clock Cycles        : {res['total_cycles']:,}")
    print(f"    - Average System CPI        : {res['average_cpi']}")
    print(f"    - System Speedup Factor     : {res['overall_speedup']}x")
    print(f"    - Throughput (TPS)          : {res['transactions_per_second']} transactions/sec")
    print(f"    - L1 I-Cache Hit Rate       : {res['i_cache_hit_rate']}%")
    print(f"    - L1 D-Cache Hit Rate       : {res['d_cache_hit_rate']}%")
    print(f"    - Branch Predictor Accuracy : {res['branch_predictor_accuracy']}%")

    print("\n[+] Fraud Decision Breakdown:")
    for dec, count in res["decisions"].items():
        print(f"    - {dec:<10}: {count} ({round(count / batch_size * 100, 1)}%)")


def print_pedagogy():
    print_banner()
    print("=== COURSE OUTCOMES (CO1–CO6) ATTAINMENT MATRIX ===")
    cos = AcademicMapping.COURSE_OUTCOMES
    for co, data in cos.items():
        print(f"\n[{co}] {data['title']} ({data['bloom_level']})")
        print(f"  Description: {data['description']}")
        print(f"  Component  : {data['implementation']}")
        print(f"  Metrics    : {', '.join(data['key_metrics'])}")

    print("\n=== COMPUTATIONAL THINKING (CT) 4 PILLARS ===")
    for p, d in AcademicMapping.COMPUTATIONAL_THINKING.items():
        print(f"\n• {p}:")
        print(f"  {d['application']}")

    print("\n=== REAL-WORLD ENGINEERING (RWE) CASE STUDIES ===")
    for title, d in AcademicMapping.REAL_WORLD_ENGINEERING.items():
        print(f"\n• {title}:")
        print(f"  Context : {d['context']}")
        print(f"  Solution: {d['architectural_solution']}")


def main():
    parser = argparse.ArgumentParser(description="Bank Fraud Architecture Simulator CLI")
    parser.add_argument("--mode", choices=["single", "batch", "rubric"], default="single",
                        help="Execution mode (single, batch, rubric)")
    parser.add_argument("--scenario", choices=["normal", "velocity_spike", "account_takeover", "impossible_travel", "large_cashout"],
                        default="velocity_spike", help="Scenario for single transaction mode")
    parser.add_argument("--batch", type=int, default=50, help="Number of transactions for batch benchmark")

    args = parser.parse_args()

    if args.mode == "single":
        run_single(scenario=args.scenario)
    elif args.mode == "batch":
        run_benchmark(batch_size=args.batch)
    elif args.mode == "rubric":
        print_pedagogy()


if __name__ == "__main__":
    main()
