"""
Pedagogical & Academic Alignment Module: CT + RWE & CO1–CO6
===========================================================
Formal definitions, assessment rubrics, and curricular mapping
for Computational Thinking (CT), Real-World Engineering (RWE),
and Course Outcomes 1 through 6.
"""

from typing import Dict, List, Any


class AcademicMapping:
    """Provides formal curricular documentation and interactive rubric metadata."""

    COURSE_OUTCOMES: Dict[str, Dict[str, Any]] = {
        "CO1": {
            "title": "Instruction Set Architecture & Machine Representation",
            "description": "Understand computer system organization, custom RISC-F instruction formatting, 32-bit binary encoding/decoding, and register file conventions.",
            "implementation": "bank_fraud_simulator.isa: Opcode enumeration, R/I/S/B/J formats, 32 general-purpose registers (R0-R31), assembly parser and disassembler.",
            "bloom_level": "Level 2 & 3 (Understand & Apply)",
            "key_metrics": ["Instruction Word Bitfields", "Addressing Modes", "Opcode Space Utilization"]
        },
        "CO2": {
            "title": "ALU & Combinational/Sequential Logic Design",
            "description": "Design arithmetic and logic circuits, 32-bit operations, condition flags (Zero, Negative, Overflow, Carry), and bitmask rule status registers.",
            "implementation": "bank_fraud_simulator.alu & logic_gates: 32-bit ALU with ADD/SUB/CMP/Bitwise operations, Status Flags [Z, N, V, C, G, L], 2:1/4:1 Mux, and FraudBitmaskLogic.",
            "bloom_level": "Level 3 & 4 (Apply & Analyze)",
            "key_metrics": ["ALU Operation Mix", "Status Flag Transitions", "Bitwise Rule Mask Precision"]
        },
        "CO3": {
            "title": "Instruction Cycle & Control Unit Sequencing",
            "description": "Analyze the 5-step instruction execution cycle (Fetch, Decode, Execute, Memory, Writeback), micro-operations in RTN, and hardwired control signals.",
            "implementation": "bank_fraud_simulator.control_unit & instruction_cycle: SingleCycleCPU with PC, IR, MAR, MDR, and ControlSignals (RegWrite, ALUSrc, MemRead, MemWrite, Branch).",
            "bloom_level": "Level 4 (Analyze)",
            "key_metrics": ["Micro-step Trace", "Control Line Signals", "Register Transfer Notation (RTN)"]
        },
        "CO4": {
            "title": "Memory Hierarchy & Cache Memory Organization",
            "description": "Evaluate multi-level cache principles, mapping techniques (Direct, Set-Associative, Fully Associative), LRU/FIFO replacement, and Average Memory Access Time (AMAT).",
            "implementation": "bank_fraud_simulator.cache: Hardware Cache class with Tag/Index/Offset splitting, LRU/FIFO policies, 3C miss classification (Compulsory, Capacity, Conflict), and AMAT calculation.",
            "bloom_level": "Level 4 & 5 (Analyze & Evaluate)",
            "key_metrics": ["Hit Rate %", "Miss Rate %", "AMAT (Cycles)", "Compulsory vs Conflict Misses"]
        },
        "CO5": {
            "title": "Pipelining & Instruction-Level Parallelism (ILP)",
            "description": "Model a 5-stage RISC pipeline, detect and mitigate RAW data hazards with forwarding/bypassing, handle load-use stalls, and resolve control hazards via 2-bit branch prediction.",
            "implementation": "bank_fraud_simulator.pipeline: PipelinedCPU with IF/ID, ID/EX, EX/MEM, MEM/WB registers, Hazard Detection Unit, Forwarding Unit, and 2-Bit Saturating Branch Predictor.",
            "bloom_level": "Level 4 & 5 (Analyze & Evaluate)",
            "key_metrics": ["Cycles Per Instruction (CPI)", "Pipeline Stalls", "Forwarding Events", "Branch Penalty Flushes"]
        },
        "CO6": {
            "title": "Quantitative Performance Evaluation & System Optimization",
            "description": "Benchmark complex banking workloads across competing microarchitectures, validate Amdahl's Law speedup, and optimize transaction throughput under financial SLAs.",
            "implementation": "bank_fraud_simulator.evaluator: Comparative analysis of 5 architectural configurations across 1,000+ transactions with Speedup, CPI, MIPS, and TPS metrics.",
            "bloom_level": "Level 5 & 6 (Evaluate & Create)",
            "key_metrics": ["Speedup Factor (S)", "Amdahl's Law Attainment", "Throughput (TPS)", "Execution Latency (µs)"]
        }
    }

    COMPUTATIONAL_THINKING: Dict[str, Dict[str, str]] = {
        "Decomposition": {
            "definition": "Breaking complex systems into modular, manageable components.",
            "application": "Decomposed monolithic banking fraud policies into atomic micro-instructions (LW, CMP, SUB, ORI, BEQ), distinct ALU arithmetic functions, independent pipeline stages, and memory cache levels."
        },
        "Pattern Recognition": {
            "definition": "Identifying similarities, recurring trends, and repeating structures.",
            "application": "Recognized that high-frequency transaction verification repeatedly queries identical rule routines and account profile parameters, creating intense temporal and spatial locality exploit-able by L1 caches."
        },
        "Abstraction": {
            "definition": "Filtering out irrelevant physical transistor details to focus on architectural models.",
            "application": "Abstracted gate-level propagation delays into discrete clock cycles, modeled pipeline inter-stage latches as typed state registers, and abstracted DRAM latencies into hit/miss cycles."
        },
        "Algorithm Design": {
            "definition": "Developing step-by-step algorithmic solutions to structural problems.",
            "application": "Designed cycle-by-cycle hazard detection logic, priority-based forwarding multiplexer selection algorithms, 2-bit saturating counter state machines, and LRU eviction trees."
        }
    }

    REAL_WORLD_ENGINEERING: Dict[str, Dict[str, str]] = {
        "Fintech Sub-Millisecond SLAs": {
            "context": "Global payment card switches (Visa/Mastercard/UPI) require sub-50ms round-trip responses. The internal fraud rules engine must complete in under 50 microseconds.",
            "architectural_solution": "Pipelined execution combined with L1 Rule (Instruction) and Profile (Data) caching drops rule verification latency from ~150 cycles down to ~35 cycles, comfortably fitting within the SLA."
        },
        "Hardware Acceleration vs Software General Compute": {
            "context": "General-purpose x86 cloud servers suffer context-switching jitter, branch misprediction stalls, and cache pollution when evaluating billions of transactions daily.",
            "architectural_solution": "Dedicated RISC-F micro-engines or FPGA/ASIC coprocessors with hardwired fraud bitmask registers enable deterministic throughput with zero OS overhead."
        },
        "Amdahl's Law in Core Banking": {
            "context": "Optimizing only CPU arithmetic yields diminishing returns if memory access to account profiles remains un-cached.",
            "architectural_solution": "Dual-caching paired with data forwarding addresses both data memory bottlenecks and pipeline data stalls, demonstrating balanced system engineering."
        }
    }

    @classmethod
    def get_summary_report(cls) -> Dict[str, Any]:
        return {
            "course_outcomes": cls.COURSE_OUTCOMES,
            "computational_thinking": cls.COMPUTATIONAL_THINKING,
            "real_world_engineering": cls.REAL_WORLD_ENGINEERING,
        }
