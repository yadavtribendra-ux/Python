"""
Arithmetic Logic Unit (ALU) Module
==================================
Simulates a 32-bit hardware ALU supporting arithmetic, logic, comparison,
and absolute difference operations with condition status flags (Z, N, V, C, G, L).

Course Outcome Mapping:
- CO2: Arithmetic and Logic Unit (ALU) design, status flags, and arithmetic algorithms.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ALUStatusFlags:
    """Hardware Status Register (PSR / Flags Register) condition codes."""
    zero: bool = False       # Z: Result is 0
    negative: bool = False   # N: MSB is 1 (negative in 2's complement)
    carry: bool = False      # C: Carry out from MSB (unsigned overflow)
    overflow: bool = False   # V: Signed 2's complement overflow
    greater: bool = False    # G: Operand 1 > Operand 2 (signed)
    less: bool = False       # L: Operand 1 < Operand 2 (signed)

    def to_dict(self) -> dict:
        return {
            "Z": int(self.zero),
            "N": int(self.negative),
            "C": int(self.carry),
            "V": int(self.overflow),
            "G": int(self.greater),
            "L": int(self.less),
        }

    def __repr__(self) -> str:
        flags = [
            f"Z={int(self.zero)}",
            f"N={int(self.negative)}",
            f"C={int(self.carry)}",
            f"V={int(self.overflow)}",
            f"G={int(self.greater)}",
            f"L={int(self.less)}",
        ]
        return f"[{' | '.join(flags)}]"


class ALU:
    """
    32-Bit Arithmetic Logic Unit for Fraud Processing.
    Simulates arithmetic (ADD, SUB, ABS_DIFF), bitwise logic (AND, OR, XOR, SLL, SRL),
    and magnitude comparisons with full flag updates.
    """
    MASK32 = 0xFFFFFFFF
    SIGN_BIT = 0x80000000

    def __init__(self):
        self.flags = ALUStatusFlags()
        self.total_operations: int = 0
        self.arithmetic_operations: int = 0
        self.logical_operations: int = 0
        self.comparison_operations: int = 0

    def reset_stats(self):
        self.total_operations = 0
        self.arithmetic_operations = 0
        self.logical_operations = 0
        self.comparison_operations = 0
        self.flags = ALUStatusFlags()

    @staticmethod
    def to_signed32(val: int) -> int:
        """Convert unsigned 32-bit integer to signed 32-bit Python int."""
        val = val & ALU.MASK32
        if val & ALU.SIGN_BIT:
            return val - 0x100000000
        return val

    @staticmethod
    def to_unsigned32(val: int) -> int:
        """Clamp / wrap integer to unsigned 32-bit range."""
        return val & ALU.MASK32

    def execute(self, alu_op: str, operand_a: int, operand_b: int) -> Tuple[int, ALUStatusFlags]:
        """
        Executes an operation on operand_a and operand_b, updates condition flags,
        and returns the 32-bit result and the updated flags.
        """
        self.total_operations += 1
        a = self.to_unsigned32(operand_a)
        b = self.to_unsigned32(operand_b)
        a_signed = self.to_signed32(a)
        b_signed = self.to_signed32(b)

        res = 0
        carry = False
        overflow = False
        op = alu_op.upper()

        if op in ("ADD", "ADDI"):
            self.arithmetic_operations += 1
            raw_sum = a + b
            res = raw_sum & self.MASK32
            carry = (raw_sum > self.MASK32)
            # Signed overflow: adding two positive numbers yields negative or vice-versa
            s_sum = a_signed + b_signed
            overflow = (s_sum > 0x7FFFFFFF) or (s_sum < -0x80000000)

        elif op in ("SUB", "SUBI"):
            self.arithmetic_operations += 1
            raw_diff = a - b
            res = raw_diff & self.MASK32
            carry = (a >= b)  # In ARM/RISC: Carry=1 on borrow clear
            s_diff = a_signed - b_signed
            overflow = (s_diff > 0x7FFFFFFF) or (s_diff < -0x80000000)

        elif op == "ABS_DIFF":
            self.arithmetic_operations += 1
            diff = abs(a_signed - b_signed)
            res = diff & self.MASK32
            carry = False
            overflow = False

        elif op in ("AND", "ANDI"):
            self.logical_operations += 1
            res = (a & b) & self.MASK32

        elif op in ("OR", "ORI"):
            self.logical_operations += 1
            res = (a | b) & self.MASK32

        elif op in ("XOR", "XORI"):
            self.logical_operations += 1
            res = (a ^ b) & self.MASK32

        elif op == "SLL":
            self.logical_operations += 1
            shamt = b & 0x1F
            res = (a << shamt) & self.MASK32

        elif op == "SRL":
            self.logical_operations += 1
            shamt = b & 0x1F
            res = (a >> shamt) & self.MASK32

        elif op in ("CMP_GT", "BGT"):
            self.comparison_operations += 1
            res = 1 if (a_signed > b_signed) else 0

        elif op in ("CMP_GE", "BGE"):
            self.comparison_operations += 1
            res = 1 if (a_signed >= b_signed) else 0

        elif op in ("CMP_LT", "SLT", "BLT"):
            self.comparison_operations += 1
            res = 1 if (a_signed < b_signed) else 0

        elif op in ("CMP_EQ", "SEQ", "BEQ"):
            self.comparison_operations += 1
            res = 1 if (a == b) else 0

        elif op in ("BNE", "SNE"):
            self.comparison_operations += 1
            res = 1 if (a != b) else 0

        elif op == "PASS_B":
            res = b & self.MASK32

        else:
            # Pass-through or default
            res = a & self.MASK32

        # Update condition flags
        res_signed = self.to_signed32(res)
        if op in ("CMP_EQ", "SEQ", "BEQ"):
            self.flags.zero = (a == b)
        elif op in ("CMP_GT", "BGT"):
            self.flags.zero = (a == b)
        elif op in ("CMP_LT", "SLT", "BLT"):
            self.flags.zero = (a == b)
        elif op in ("CMP_GE", "BGE"):
            self.flags.zero = (a == b)
        else:
            self.flags.zero = (res == 0)

        self.flags.negative = bool(res & self.SIGN_BIT) if op not in ("CMP_GT", "CMP_LT", "CMP_GE", "CMP_EQ", "BEQ", "BNE") else (a_signed < b_signed)
        self.flags.carry = carry
        self.flags.overflow = overflow
        self.flags.greater = (a_signed > b_signed)
        self.flags.less = (a_signed < b_signed)

        return res, self.flags
