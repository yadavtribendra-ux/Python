"""
Control Unit Module
===================
Simulates the Hardwired Control Unit generating micro-control signals
for the RISC-F Datapath across the Instruction Cycle.

Course Outcome Mapping:
- CO3: Instruction cycle, control unit design, and micro-operation sequencing.
"""

from dataclasses import dataclass
from typing import Dict, Any
from .isa import Opcode, Instruction


@dataclass
class ControlSignals:
    reg_write: bool = False
    alu_src: bool = False       # 0: Register (Rs2), 1: Immediate
    alu_op: str = "ADD"
    mem_read: bool = False
    mem_write: bool = False
    mem_to_reg: bool = False    # 0: ALU Result, 1: Memory Data
    branch: bool = False
    jump: bool = False
    halt: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "RegWrite": int(self.reg_write),
            "ALUSrc": int(self.alu_src),
            "ALUOp": self.alu_op,
            "MemRead": int(self.mem_read),
            "MemWrite": int(self.mem_write),
            "MemToReg": int(self.mem_to_reg),
            "Branch": int(self.branch),
            "Jump": int(self.jump),
            "Halt": int(self.halt),
        }


class ControlUnit:
    """Decodes Instruction opcode and generates datapath control signals."""

    @staticmethod
    def generate_signals(inst: Instruction) -> ControlSignals:
        signals = ControlSignals()
        op = inst.opcode

        if op == Opcode.NOP:
            return signals

        if op == Opcode.HALT:
            signals.halt = True
            return signals

        # R-Type Arithmetic & Logic
        if op.format_type == "R":
            signals.reg_write = True
            signals.alu_src = False
            signals.mem_to_reg = False
            signals.alu_op = op.name
            return signals

        # I-Type Arithmetic & Logic & Comparisons
        if op in (Opcode.ADDI, Opcode.SUBI, Opcode.ANDI, Opcode.ORI, Opcode.XORI,
                  Opcode.CMP_GT, Opcode.CMP_GE, Opcode.CMP_LT, Opcode.CMP_EQ):
            signals.reg_write = True
            signals.alu_src = True
            signals.mem_to_reg = False
            signals.alu_op = op.name
            return signals

        # Memory Load Word
        if op == Opcode.LW:
            signals.reg_write = True
            signals.alu_src = True
            signals.mem_read = True
            signals.mem_to_reg = True
            signals.alu_op = "ADD"  # Effective address calculation: Rs1 + Imm
            return signals

        # Memory Store Word
        if op == Opcode.SW:
            signals.reg_write = False
            signals.alu_src = True
            signals.mem_write = True
            signals.alu_op = "ADD"  # Effective address: Rs1 + Imm
            return signals

        # Branch Instructions
        if op.format_type == "B":
            signals.reg_write = False
            signals.alu_src = False
            signals.branch = True
            signals.alu_op = op.name  # Subtraction / comparison in ALU
            return signals

        # Jump Instructions
        if op == Opcode.JMP:
            signals.jump = True
            signals.reg_write = False
            return signals

        return signals
