"""
Banking Fraud Rules & Assembly Microcode Suite
==============================================
Defines standard banking fraud evaluation rules compiled into
RISC-F assembly instructions for evaluation on CPU pipeline and cache.

Course Outcome Mapping:
- CO1: Program representation and instruction sequencing.
- CO2: Arithmetic and logical rule evaluation.
- CO5: Pipeline hazard patterns (RAW, Load-Use, Branching) in real workloads.
"""

from typing import List, Dict, Any
from .isa import Instruction, parse_assembly
from .logic_gates import FraudBitmaskLogic


class BankFraudRules:
    """
    Standard Financial Fraud Detection Ruleset in RISC-F Assembly.
    Base Address Registers:
      - R28: Memory-Mapped Transaction Buffer (0x2000)
      - R29: Memory-Mapped Decision Buffer (0x3000)
    """

    @staticmethod
    def get_standard_assembly_program(
        large_limit: int = 50000,
        rapid_limit: int = 5,
        pin_limit: int = 3,
        speed_limit: int = 800,
        risk_threshold_review: int = 4,
        risk_threshold_reject: int = 6,
    ) -> str:
        """
        Generates assembly program implementing complete bank fraud evaluation.
        Demonstrates repeated arithmetic and logical rule execution.
        """
        return f"""
        ; ==============================================================
        ; BANK FRAUD-RULE PROCESSING ARCHITECTURE ENGINE: RISC-F CODE
        ; Evaluates repeated arithmetic & logical transaction rules
        ; ==============================================================

        ; ---------------- INITIALIZATION ----------------
        ADDI  R28, R0, #8192     ; R28 = 0x2000 (Base Txn MMIO)
        ADDI  R29, R0, #12288    ; R29 = 0x3000 (Base Decision MMIO)
        ADDI  R8, R0, #0         ; R8 = Risk Score Accumulator = 0
        ADDI  R9, R0, #0         ; R9 = Fraud Status Bitmask = 0

        ; ---------------- RULE 1: VELOCITY SPIKE (ARITHMETIC) ----------------
        ; Check if recent transactions frequency >= rapid_limit
        LW    R3, 8(R28)         ; Load frequency from MMIO [0x2008]
        CMP_GE R10, R3, #{rapid_limit} ; ALU Comparison: R3 >= rapid_limit
        BEQ   R10, R0, SKIP_R1   ; Branch if condition false
        ORI   R9, R9, #2         ; Assert Flag Bit 1 (Velocity Spike)
        ADDI  R8, R8, #2         ; Risk Score += 2
SKIP_R1:

        ; ---------------- RULE 2: LARGE AMOUNT & OVERDRAFT (ARITHMETIC) ----------------
        ; Arithmetic delta: Balance - Amount
        LW    R1, 0(R28)         ; Load Amount from MMIO [0x2000]
        LW    R2, 4(R28)         ; Load Available Balance from MMIO [0x2004]
        SUB   R11, R2, R1        ; ALU Subtraction: R11 = Balance - Amount
        BLT   R11, R0, DEFICIT   ; If Remaining < 0 (Insufficient Balance)
        CMP_GE R10, R1, #{large_limit} ; ALU Comparison: Amount >= large_limit
        BEQ   R10, R0, SKIP_R2   ; Branch if condition false
        ORI   R9, R9, #1         ; Assert Flag Bit 0 (Large Amount Outlier)
        ADDI  R8, R8, #2         ; Risk Score += 2
        JMP   SKIP_R2
DEFICIT:
        ORI   R9, R9, #32        ; Assert Flag Bit 5 (Balance Deficit)
        ADDI  R8, R8, #4         ; Risk Score += 4
SKIP_R2:

        ; ---------------- RULE 3: GEO-VELOCITY SPEED CHECK (ARITHMETIC) ----------------
        ; Distance / Time > speed_limit (e.g. 800 km/h impossible physical speed)
        LW    R5, 16(R28)        ; Load Geo-Speed from MMIO [0x2010]
        CMP_GT R10, R5, #{speed_limit} ; ALU Comparison: Speed > speed_limit
        BEQ   R10, R0, SKIP_R3   ; Branch if not exceeded
        ORI   R9, R9, #4         ; Assert Flag Bit 2 (Geo Impossible)
        ADDI  R8, R8, #5         ; High Risk += 5
SKIP_R3:

        ; ---------------- RULE 4: AUTHENTICATION / PIN FAILURES (LOGIC & ARITHMETIC) ----------------
        ; Check if failed PIN attempts >= pin_limit
        LW    R4, 12(R28)        ; Load Failed PINs from MMIO [0x200C]
        CMP_GE R10, R4, #{pin_limit} ; ALU Comparison: Failed PINs >= pin_limit
        BEQ   R10, R0, SKIP_R4   ; Branch if condition false
        ORI   R9, R9, #8         ; Assert Flag Bit 3 (Auth Failure)
        ADDI  R8, R8, #3         ; Risk Score += 3
SKIP_R4:

        ; ---------------- RULE 5: UNRECOGNIZED DEVICE & OFF-HOURS (LOGIC BITMASK) ----------------
        ; Check Device Trust (0 = untrusted device)
        LW    R7, 24(R28)        ; Load Device Trust Flag from MMIO [0x2018]
        BNE   R7, R0, SKIP_R5    ; Branch if device is trusted (R7 != 0)
        ORI   R9, R9, #16        ; Assert Flag Bit 4 (Device Untrusted)
        ADDI  R8, R8, #2         ; Risk Score += 2
SKIP_R5:

        ; ---------------- RULE 6: COMPOSITE DECISION & WRITEBACK ----------------
        ; Output decision: 1 = APPROVE, 2 = REVIEW, 3 = REJECT
        SW    R8, 0(R29)         ; Store Risk Score at [0x3000]
        SW    R9, 4(R29)         ; Store Fraud Flag Mask at [0x3004]

        CMP_GE R10, R8, #{risk_threshold_reject} ; Risk >= Reject threshold?
        BNE   R10, R0, ACTION_REJECT

        CMP_GE R10, R8, #{risk_threshold_review} ; Risk >= Review threshold?
        BNE   R10, R0, ACTION_REVIEW

        ; Action: APPROVE
        ADDI  R12, R0, #1        ; Code 1: APPROVE
        SW    R12, 8(R29)        ; Write Decision to [0x3008]
        HALT

ACTION_REVIEW:
        ADDI  R12, R0, #2        ; Code 2: REVIEW
        SW    R12, 8(R29)        ; Write Decision to [0x3008]
        HALT

ACTION_REJECT:
        ADDI  R12, R0, #3        ; Code 3: REJECT
        SW    R12, 8(R29)        ; Write Decision to [0x3008]
        HALT
        """

    @classmethod
    def compile_rules(cls, **kwargs) -> List[Instruction]:
        """Assembles the fraud rules assembly code into binary instructions."""
        asm_code = cls.get_standard_assembly_program(**kwargs)
        return parse_assembly(asm_code)
