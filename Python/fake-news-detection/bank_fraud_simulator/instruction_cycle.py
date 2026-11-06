"""
Instruction Cycle & Single-Cycle Processor Module
================================================
Simulates the classical Von Neumann instruction cycle:
Fetch -> Decode -> Execute -> Memory Access -> Write Back.
Maintains architectural state (PC, IR, MAR, MDR, Register File, Flags).

Course Outcome Mapping:
- CO1: Register organization and data paths.
- CO3: Instruction cycle, micro-operations, and register transfer notation (RTN).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .isa import Instruction, Opcode
from .alu import ALU, ALUStatusFlags
from .control_unit import ControlUnit, ControlSignals
from .memory import Memory
from .cache import Cache


@dataclass
class MicroStepLog:
    """Detailed micro-operation log for pedagogical display."""
    cycle: int
    pc: int
    phase: str          # FETCH, DECODE, EXECUTE, MEMORY, WRITEBACK
    micro_op: str       # e.g., "MAR <- PC, IR <- Mem[MAR]"
    description: str
    reg_changes: str = ""
    flags: str = ""


class SingleCycleCPU:
    """
    Simulates a baseline single-cycle processor executing RISC-F instructions.
    Provides complete register transfer level (RTL) inspection for academic evaluation.
    """
    def __init__(self, memory: Memory, cache: Optional[Cache] = None):
        self.memory = memory
        self.cache = cache
        self.alu = ALU()
        self.registers: List[int] = [0] * 32  # R0 - R31
        self.pc: int = 0
        self.ir: Optional[Instruction] = None
        self.mar: int = 0
        self.mdr: int = 0
        self.halted: bool = False
        self.cycles: int = 0
        self.instructions_executed: int = 0
        self.cycle_log: List[MicroStepLog] = []

    def reset(self):
        self.registers = [0] * 32
        self.pc = 0
        self.ir = None
        self.mar = 0
        self.mdr = 0
        self.halted = False
        self.cycles = 0
        self.instructions_executed = 0
        self.cycle_log = []
        self.alu.reset_stats()
        if self.cache:
            self.cache.reset()

    def set_register(self, reg_idx: int, val: int):
        if reg_idx == 0:
            return  # R0 is hardwired to 0
        self.registers[reg_idx & 0x1F] = val & 0xFFFFFFFF

    def get_register(self, reg_idx: int) -> int:
        if reg_idx == 0:
            return 0
        return self.registers[reg_idx & 0x1F]

    def step(self, program: List[Instruction]) -> bool:
        """
        Executes one full instruction cycle for the current instruction at self.pc.
        Returns True if program continues, False if HALT or out of bounds.
        """
        if self.halted:
            return False

        # Find instruction at PC
        inst_idx = self.pc // 4
        if inst_idx < 0 or inst_idx >= len(program):
            self.halted = True
            return False

        self.ir = program[inst_idx]
        current_inst = self.ir
        self.cycles += 1
        curr_cycle = self.cycles
        prev_pc = self.pc

        # ---------------- 1. FETCH PHASE ----------------
        self.mar = self.pc
        # Model memory / cache access for instruction fetch
        fetch_cycles = 1
        if self.cache:
            cache_res = self.cache.access(self.mar, is_write=False)
            fetch_cycles = cache_res.cycles_spent

        self.cycle_log.append(MicroStepLog(
            cycle=curr_cycle,
            pc=prev_pc,
            phase="FETCH",
            micro_op=f"MAR <- 0x{self.mar:04X}; IR <- Mem[MAR]; PC <- PC + 4",
            description=f"Fetched '{current_inst.disassemble()}' from address 0x{self.mar:04X}",
            flags=str(self.alu.flags)
        ))
        next_pc = self.pc + 4

        # ---------------- 2. DECODE PHASE ----------------
        signals = ControlUnit.generate_signals(current_inst)
        rs1_val = self.get_register(current_inst.rs1)
        rs2_val = self.get_register(current_inst.rs2)
        imm_val = current_inst.imm

        self.cycle_log.append(MicroStepLog(
            cycle=curr_cycle,
            pc=prev_pc,
            phase="DECODE",
            micro_op=f"Decode {current_inst.opcode.name}; Read R{current_inst.rs1}={rs1_val}, R{current_inst.rs2}={rs2_val}",
            description=f"Control signals: RegWrite={signals.reg_write}, ALUSrc={signals.alu_src}, MemRead={signals.mem_read}",
            flags=str(self.alu.flags)
        ))

        if signals.halt:
            self.halted = True
            self.instructions_executed += 1
            return False

        # ---------------- 3. EXECUTE PHASE ----------------
        # Operand B MUX: Register or Immediate
        operand_b = imm_val if signals.alu_src else rs2_val
        alu_result, flags = self.alu.execute(signals.alu_op, rs1_val, operand_b)

        branch_taken = False
        if signals.branch:
            # Branch conditions based on ALU flags
            if current_inst.opcode == Opcode.BEQ:
                branch_taken = flags.zero
            elif current_inst.opcode == Opcode.BNE:
                branch_taken = not flags.zero
            elif current_inst.opcode == Opcode.BGT:
                branch_taken = flags.greater
            elif current_inst.opcode == Opcode.BLT:
                branch_taken = flags.less
            elif current_inst.opcode == Opcode.BGE:
                branch_taken = flags.greater or flags.zero

            if branch_taken:
                # Target PC calculation: PC + branch_offset * 4
                next_pc = self.pc + (imm_val * 4)

        if signals.jump:
            next_pc = imm_val

        self.cycle_log.append(MicroStepLog(
            cycle=curr_cycle,
            pc=prev_pc,
            phase="EXECUTE",
            micro_op=f"ALU_OUT <- {rs1_val} {signals.alu_op} {operand_b} => {alu_result}",
            description=f"Flags: Z={int(flags.zero)} N={int(flags.negative)} V={int(flags.overflow)} C={int(flags.carry)}"
                        + (f" | Branch TAKEN to 0x{next_pc:04X}" if branch_taken else (" | Branch NOT taken" if signals.branch else "")),
            flags=str(flags)
        ))

        # ---------------- 4. MEMORY ACCESS PHASE ----------------
        mem_data = 0
        if signals.mem_read:
            self.mar = alu_result
            if self.cache:
                c_res = self.cache.access(self.mar, is_write=False)
                fetch_cycles += c_res.cycles_spent - 1
            mem_data = self.memory.read_word(self.mar)
            self.mdr = mem_data
            self.cycle_log.append(MicroStepLog(
                cycle=curr_cycle,
                pc=prev_pc,
                phase="MEMORY",
                micro_op=f"MAR <- 0x{self.mar:04X}; MDR <- Mem[MAR] => {mem_data}",
                description=f"Read word {mem_data} from memory address 0x{self.mar:04X}",
                flags=str(flags)
            ))
        elif signals.mem_write:
            self.mar = alu_result
            self.mdr = rs2_val
            if self.cache:
                c_res = self.cache.access(self.mar, is_write=True, write_data=self.mdr)
                fetch_cycles += c_res.cycles_spent - 1
            self.memory.write_word(self.mar, self.mdr)
            self.cycle_log.append(MicroStepLog(
                cycle=curr_cycle,
                pc=prev_pc,
                phase="MEMORY",
                micro_op=f"MAR <- 0x{self.mar:04X}; Mem[MAR] <- MDR (value={self.mdr})",
                description=f"Wrote word {self.mdr} to address 0x{self.mar:04X}",
                flags=str(flags)
            ))
        else:
            self.cycle_log.append(MicroStepLog(
                cycle=curr_cycle,
                pc=prev_pc,
                phase="MEMORY",
                micro_op="No Memory Access",
                description="Instruction does not access data memory",
                flags=str(flags)
            ))

        # ---------------- 5. WRITEBACK PHASE ----------------
        reg_delta = ""
        if signals.reg_write and current_inst.rd != 0:
            write_value = mem_data if signals.mem_to_reg else alu_result
            self.set_register(current_inst.rd, write_value)
            reg_delta = f"R{current_inst.rd} = {write_value}"
            self.cycle_log.append(MicroStepLog(
                cycle=curr_cycle,
                pc=prev_pc,
                phase="WRITEBACK",
                micro_op=f"R{current_inst.rd} <- {write_value}",
                description=f"Stored {'Memory Data' if signals.mem_to_reg else 'ALU Result'} into R{current_inst.rd}",
                reg_changes=reg_delta,
                flags=str(flags)
            ))
        else:
            self.cycle_log.append(MicroStepLog(
                cycle=curr_cycle,
                pc=prev_pc,
                phase="WRITEBACK",
                micro_op="No Register Write",
                description="Destination register is R0 or RegWrite disabled",
                flags=str(flags)
            ))

        # Update Program Counter
        self.pc = next_pc
        self.instructions_executed += 1
        return True

    def run(self, program: List[Instruction], max_cycles: int = 1000) -> int:
        """Runs the program to completion or max_cycles."""
        count = 0
        while count < max_cycles and not self.halted:
            if not self.step(program):
                break
            count += 1
        return self.instructions_executed
