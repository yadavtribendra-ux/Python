"""
Pipelined Processor Subsystem Module
====================================
Simulates a cycle-accurate 5-Stage Classic RISC Pipeline:
[IF] -> [ID] -> [EX] -> [MEM] -> [WB]

Includes:
- Pipeline Inter-stage Registers (IF/ID, ID/EX, EX/MEM, MEM/WB)
- Hazard Detection Unit (RAW Data Hazards, Load-Use Stalls)
- Data Forwarding Unit (EX-to-EX, MEM-to-EX bypasses)
- Dynamic 2-Bit Saturating Counter Branch Predictor & Branch Target Buffer (BTB)
- Pipeline Timing Matrix / Gantt Chart generation for cycle-by-cycle visualization.

Course Outcome Mapping:
- CO5: Pipelining principles, pipeline hazards (structural, data, control),
  forwarding/bypassing, branch prediction, and pipeline performance evaluation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from .isa import Instruction, Opcode
from .alu import ALU, ALUStatusFlags
from .control_unit import ControlUnit, ControlSignals
from .memory import Memory
from .cache import Cache


class BranchPredictorMode(Enum):
    ALWAYS_NOT_TAKEN = "Always Not Taken (Static)"
    ALWAYS_TAKEN     = "Always Taken (Static)"
    DYNAMIC_2BIT     = "Dynamic 2-Bit Saturating Counter"


class TwoBitBranchPredictor:
    """
    2-bit Saturating Counter Branch Predictor.
    States:
      00: Strongly Not Taken (SNT)
      01: Weakly Not Taken (WNT)
      10: Weakly Taken (WT)
      11: Strongly Taken (ST)
    """
    def __init__(self):
        self.table: Dict[int, int] = {}  # PC -> 2-bit state (0..3)
        self.btb: Dict[int, int] = {}    # Branch Target Buffer: PC -> Target Addr
        self.predictions: int = 0
        self.correct_predictions: int = 0

    def predict(self, pc: int) -> Tuple[bool, int]:
        """Returns (predicted_taken, predicted_target_pc)."""
        self.predictions += 1
        state = self.table.get(pc, 1)  # Default: Weakly Not Taken (01)
        taken = (state >= 2)
        target = self.btb.get(pc, pc + 4)
        return taken, target

    def update(self, pc: int, actual_taken: bool, actual_target: int):
        """Updates saturating counter state and BTB entry."""
        state = self.table.get(pc, 1)
        predicted = (state >= 2)
        if predicted == actual_taken:
            self.correct_predictions += 1

        # State transition
        if actual_taken:
            new_state = min(3, state + 1)
            self.btb[pc] = actual_target
        else:
            new_state = max(0, state - 1)

        self.table[pc] = new_state

    @property
    def accuracy(self) -> float:
        return (self.correct_predictions / self.predictions) if self.predictions > 0 else 1.0


# -------------------- PIPELINE REGISTERS --------------------

@dataclass
class IF_ID_Register:
    valid: bool = False
    pc: int = 0
    instruction: Optional[Instruction] = None
    predicted_taken: bool = False


@dataclass
class ID_EX_Register:
    valid: bool = False
    pc: int = 0
    instruction: Optional[Instruction] = None
    signals: ControlSignals = field(default_factory=ControlSignals)
    rs1_val: int = 0
    rs2_val: int = 0
    rs1_idx: int = 0
    rs2_idx: int = 0
    rd_idx: int = 0
    imm: int = 0
    predicted_taken: bool = False


@dataclass
class EX_MEM_Register:
    valid: bool = False
    pc: int = 0
    instruction: Optional[Instruction] = None
    signals: ControlSignals = field(default_factory=ControlSignals)
    alu_result: int = 0
    write_data: int = 0  # Store data
    rd_idx: int = 0
    flags: ALUStatusFlags = field(default_factory=ALUStatusFlags)
    branch_taken: bool = False
    branch_target: int = 0


@dataclass
class MEM_WB_Register:
    valid: bool = False
    pc: int = 0
    instruction: Optional[Instruction] = None
    signals: ControlSignals = field(default_factory=ControlSignals)
    alu_result: int = 0
    mem_read_data: int = 0
    rd_idx: int = 0


@dataclass
class CycleSnapshot:
    cycle: int
    if_inst: str
    id_inst: str
    ex_inst: str
    mem_inst: str
    wb_inst: str
    stall: bool
    flush: bool
    forward_a: str
    forward_b: str
    pc: int
    note: str = ""


class PipelinedCPU:
    """
    Cycle-Accurate 5-Stage Pipelined Processor.
    Supports toggling of Forwarding, Branch Prediction, and Cache hierarchy.
    """
    def __init__(
        self,
        memory: Memory,
        i_cache: Optional[Cache] = None,
        d_cache: Optional[Cache] = None,
        enable_forwarding: bool = True,
        branch_predictor_mode: BranchPredictorMode = BranchPredictorMode.DYNAMIC_2BIT,
    ):
        self.memory = memory
        self.i_cache = i_cache
        self.d_cache = d_cache
        self.enable_forwarding = enable_forwarding
        self.branch_predictor_mode = branch_predictor_mode
        self.branch_predictor = TwoBitBranchPredictor()
        self.alu = ALU()

        # Architectural registers (R0-R31)
        self.registers: List[int] = [0] * 32

        # Pipeline Registers
        self.if_id = IF_ID_Register()
        self.id_ex = ID_EX_Register()
        self.ex_mem = EX_MEM_Register()
        self.mem_wb = MEM_WB_Register()

        # Program Counter and status
        self.pc: int = 0
        self.cycle_count: int = 0
        self.instructions_retired: int = 0
        self.stall_cycles: int = 0
        self.flush_cycles: int = 0
        self.forward_a_events: int = 0
        self.forward_b_events: int = 0
        self.halted: bool = False

        # Visual Gantt chart and snapshots
        self.snapshots: List[CycleSnapshot] = []
        # instruction index -> list of stages per cycle
        self.gantt_records: Dict[int, Dict[int, str]] = {}

    def reset(self):
        self.registers = [0] * 32
        self.if_id = IF_ID_Register()
        self.id_ex = ID_EX_Register()
        self.ex_mem = EX_MEM_Register()
        self.mem_wb = MEM_WB_Register()
        self.pc = 0
        self.cycle_count = 0
        self.instructions_retired = 0
        self.stall_cycles = 0
        self.flush_cycles = 0
        self.forward_a_events = 0
        self.forward_b_events = 0
        self.halted = False
        self.snapshots.clear()
        self.gantt_records.clear()
        self.alu.reset_stats()
        self.branch_predictor = TwoBitBranchPredictor()
        if self.i_cache:
            self.i_cache.reset()
        if self.d_cache:
            self.d_cache.reset()

    def get_register(self, reg_idx: int) -> int:
        if reg_idx == 0:
            return 0
        return self.registers[reg_idx & 0x1F]

    def set_register(self, reg_idx: int, val: int):
        if reg_idx == 0:
            return
        self.registers[reg_idx & 0x1F] = val & 0xFFFFFFFF

    def clock_tick(self, program: List[Instruction]) -> bool:
        """
        Executes one clock cycle across all 5 pipeline stages simultaneously.
        Stages are evaluated in reverse order (WB -> MEM -> EX -> ID -> IF)
        to prevent race conditions on inter-stage registers.
        """
        if self.halted:
            return False

        self.cycle_count += 1
        curr_cycle = self.cycle_count
        note = ""

        # Default controls for this cycle
        stall_pipeline = False
        flush_pipeline = False
        forward_a_src = "None"
        forward_b_src = "None"

        # ---------------- 5. WRITE-BACK STAGE (WB) ----------------
        retired_inst_wb = None
        if self.mem_wb.valid:
            wb_inst = self.mem_wb.instruction
            retired_inst_wb = wb_inst
            signals = self.mem_wb.signals

            if signals.halt:
                self.halted = True

            if signals.reg_write and self.mem_wb.rd_idx != 0:
                write_val = self.mem_wb.mem_read_data if signals.mem_to_reg else self.mem_wb.alu_result
                self.set_register(self.mem_wb.rd_idx, write_val)

            self.instructions_retired += 1
            if wb_inst:
                inst_idx = wb_inst.address // 4
                self.gantt_records.setdefault(inst_idx, {})[curr_cycle] = "WB"

        # ---------------- 4. MEMORY STAGE (MEM) ----------------
        new_mem_wb = MEM_WB_Register()
        if self.ex_mem.valid:
            mem_inst = self.ex_mem.instruction
            signals = self.ex_mem.signals
            alu_res = self.ex_mem.alu_result
            write_data = self.ex_mem.write_data
            read_data = 0

            if mem_inst:
                inst_idx = mem_inst.address // 4
                self.gantt_records.setdefault(inst_idx, {})[curr_cycle] = "MEM"

            if signals.mem_read:
                if self.d_cache:
                    self.d_cache.access(alu_res, is_write=False)
                read_data = self.memory.read_word(alu_res)

            elif signals.mem_write:
                if self.d_cache:
                    self.d_cache.access(alu_res, is_write=True, write_data=write_data)
                self.memory.write_word(alu_res, write_data)

            new_mem_wb.valid = True
            new_mem_wb.pc = self.ex_mem.pc
            new_mem_wb.instruction = mem_inst
            new_mem_wb.signals = signals
            new_mem_wb.alu_result = alu_res
            new_mem_wb.mem_read_data = read_data
            new_mem_wb.rd_idx = self.ex_mem.rd_idx

        # ---------------- 3. EXECUTE STAGE (EX) ----------------
        new_ex_mem = EX_MEM_Register()
        branch_resolved = False
        branch_mispredicted = False
        correct_target_pc = 0

        if self.id_ex.valid:
            ex_inst = self.id_ex.instruction
            signals = self.id_ex.signals
            inst_idx = ex_inst.address // 4 if ex_inst else 0
            self.gantt_records.setdefault(inst_idx, {})[curr_cycle] = "EX"

            op_a = self.id_ex.rs1_val
            op_b = self.id_ex.rs2_val

            # FORWARDING UNIT LOGIC
            if self.enable_forwarding:
                # Forwarding to ALU Input A:
                # Check EX Hazard (Forward from EX/MEM)
                if (self.ex_mem.valid and self.ex_mem.signals.reg_write and
                        self.ex_mem.rd_idx != 0 and self.ex_mem.rd_idx == self.id_ex.rs1_idx):
                    op_a = self.ex_mem.alu_result
                    forward_a_src = "EX/MEM"
                    self.forward_a_events += 1
                # Check MEM Hazard (Forward from MEM/WB)
                elif (self.mem_wb.valid and self.mem_wb.signals.reg_write and
                      self.mem_wb.rd_idx != 0 and self.mem_wb.rd_idx == self.id_ex.rs1_idx):
                    op_a = self.mem_wb.mem_read_data if self.mem_wb.signals.mem_to_reg else self.mem_wb.alu_result
                    forward_a_src = "MEM/WB"
                    self.forward_a_events += 1

                # Forwarding to ALU Input B:
                # Check EX Hazard
                if (self.ex_mem.valid and self.ex_mem.signals.reg_write and
                        self.ex_mem.rd_idx != 0 and self.ex_mem.rd_idx == self.id_ex.rs2_idx):
                    op_b = self.ex_mem.alu_result
                    forward_b_src = "EX/MEM"
                    self.forward_b_events += 1
                elif (self.mem_wb.valid and self.mem_wb.signals.reg_write and
                      self.mem_wb.rd_idx != 0 and self.mem_wb.rd_idx == self.id_ex.rs2_idx):
                    op_b = self.mem_wb.mem_read_data if self.mem_wb.signals.mem_to_reg else self.mem_wb.alu_result
                    forward_b_src = "MEM/WB"
                    self.forward_b_events += 1

            # Prepare ALU inputs (MUX with Immediate)
            alu_in_b = self.id_ex.imm if signals.alu_src else op_b
            alu_res, flags = self.alu.execute(signals.alu_op, op_a, alu_in_b)

            # BRANCH EVALUATION & RESOLUTION
            actual_taken = False
            if signals.branch:
                branch_resolved = True
                if ex_inst.opcode == Opcode.BEQ:
                    actual_taken = flags.zero
                elif ex_inst.opcode == Opcode.BNE:
                    actual_taken = not flags.zero
                elif ex_inst.opcode == Opcode.BGT:
                    actual_taken = flags.greater
                elif ex_inst.opcode == Opcode.BLT:
                    actual_taken = flags.less
                elif ex_inst.opcode == Opcode.BGE:
                    actual_taken = flags.greater or flags.zero

                actual_target = self.id_ex.pc + (self.id_ex.imm * 4) if actual_taken else self.id_ex.pc + 4

                # Check prediction
                if self.branch_predictor_mode == BranchPredictorMode.DYNAMIC_2BIT:
                    self.branch_predictor.update(self.id_ex.pc, actual_taken, actual_target)

                if actual_taken != self.id_ex.predicted_taken:
                    branch_mispredicted = True
                    flush_pipeline = True
                    correct_target_pc = actual_target
                    self.flush_cycles += 1
                    note = f"Branch Misprediction! Flushing IF/ID and ID/EX (Jump to 0x{correct_target_pc:04X})"

            if signals.jump:
                correct_target_pc = self.id_ex.imm
                flush_pipeline = True
                self.flush_cycles += 1
                note = f"Unconditional Jump! PC -> 0x{correct_target_pc:04X}"

            new_ex_mem.valid = True
            new_ex_mem.pc = self.id_ex.pc
            new_ex_mem.instruction = ex_inst
            new_ex_mem.signals = signals
            new_ex_mem.alu_result = alu_res
            new_ex_mem.write_data = op_b  # Store data
            new_ex_mem.rd_idx = self.id_ex.rd_idx
            new_ex_mem.flags = flags
            new_ex_mem.branch_taken = actual_taken
            new_ex_mem.branch_target = actual_target if actual_taken else self.id_ex.pc + 4

        # ---------------- 2. DECODE STAGE (ID) ----------------
        new_id_ex = ID_EX_Register()
        if self.if_id.valid:
            id_inst = self.if_id.instruction
            inst_idx = id_inst.address // 4 if id_inst else 0
            signals = ControlUnit.generate_signals(id_inst)

            # HAZARD DETECTION UNIT (Data Hazards & Load-Use)
            load_use_hazard = False
            # Check Load-Use Hazard:
            if self.id_ex.valid and self.id_ex.signals.mem_read:
                if self.id_ex.rd_idx != 0 and (self.id_ex.rd_idx == id_inst.rs1 or
                   (self.id_ex.rd_idx == id_inst.rs2 and not signals.alu_src)):
                    load_use_hazard = True

            # If forwarding is DISABLED, any RAW hazard requires stalling!
            raw_stall = False
            if not self.enable_forwarding:
                # Check EX stage dependency
                if self.id_ex.valid and self.id_ex.signals.reg_write and self.id_ex.rd_idx != 0:
                    if self.id_ex.rd_idx == id_inst.rs1 or (self.id_ex.rd_idx == id_inst.rs2 and not signals.alu_src):
                        raw_stall = True
                # Check MEM stage dependency
                if self.ex_mem.valid and self.ex_mem.signals.reg_write and self.ex_mem.rd_idx != 0:
                    if self.ex_mem.rd_idx == id_inst.rs1 or (self.ex_mem.rd_idx == id_inst.rs2 and not signals.alu_src):
                        raw_stall = True

            if load_use_hazard or raw_stall:
                # STALL PIPELINE: Insert Bubble into ID/EX, Hold IF/ID and PC!
                stall_pipeline = True
                self.stall_cycles += 1
                new_id_ex.valid = False  # Insert bubble (NOP)
                self.gantt_records.setdefault(inst_idx, {})[curr_cycle] = "STALL"
                note = "Load-Use Hazard Stall (1-cycle bubble)" if load_use_hazard else "RAW Data Hazard Stall (No-Forwarding)"
            else:
                self.gantt_records.setdefault(inst_idx, {})[curr_cycle] = "ID"
                rs1_val = self.get_register(id_inst.rs1)
                rs2_val = self.get_register(id_inst.rs2)

                # WB forwarding directly to decode register read (Internal Register Forwarding)
                if self.mem_wb.valid and self.mem_wb.signals.reg_write and self.mem_wb.rd_idx != 0:
                    wb_res = self.mem_wb.mem_read_data if self.mem_wb.signals.mem_to_reg else self.mem_wb.alu_result
                    if self.mem_wb.rd_idx == id_inst.rs1:
                        rs1_val = wb_res
                    if self.mem_wb.rd_idx == id_inst.rs2:
                        rs2_val = wb_res

                new_id_ex.valid = True
                new_id_ex.pc = self.if_id.pc
                new_id_ex.instruction = id_inst
                new_id_ex.signals = signals
                new_id_ex.rs1_val = rs1_val
                new_id_ex.rs2_val = rs2_val
                new_id_ex.rs1_idx = id_inst.rs1
                new_id_ex.rs2_idx = id_inst.rs2
                new_id_ex.rd_idx = id_inst.rd
                new_id_ex.imm = id_inst.imm
                new_id_ex.predicted_taken = self.if_id.predicted_taken

        # ---------------- 1. FETCH STAGE (IF) ----------------
        new_if_id = IF_ID_Register()
        inst_idx_fetch = self.pc // 4

        if not stall_pipeline:
            if 0 <= inst_idx_fetch < len(program):
                fetched_inst = program[inst_idx_fetch]
                if self.i_cache:
                    self.i_cache.access(self.pc, is_write=False)

                self.gantt_records.setdefault(inst_idx_fetch, {})[curr_cycle] = "IF"

                predicted_taken = False
                predicted_target = self.pc + 4

                if fetched_inst.opcode.format_type == "B":
                    if self.branch_predictor_mode == BranchPredictorMode.ALWAYS_TAKEN:
                        predicted_taken = True
                        predicted_target = self.pc + (fetched_inst.imm * 4)
                    elif self.branch_predictor_mode == BranchPredictorMode.DYNAMIC_2BIT:
                        predicted_taken, predicted_target = self.branch_predictor.predict(self.pc)

                new_if_id.valid = True
                new_if_id.pc = self.pc
                new_if_id.instruction = fetched_inst
                new_if_id.predicted_taken = predicted_taken

                # Update PC
                if branch_mispredicted or (self.id_ex.valid and self.id_ex.signals.jump):
                    self.pc = correct_target_pc
                elif predicted_taken:
                    self.pc = predicted_target
                else:
                    self.pc += 4
            else:
                # Program finished or beyond boundaries
                if branch_mispredicted or (self.id_ex.valid and self.id_ex.signals.jump):
                    self.pc = correct_target_pc
                new_if_id.valid = False
        else:
            # Retain IF/ID on stall
            new_if_id = self.if_id
            if 0 <= inst_idx_fetch < len(program):
                self.gantt_records.setdefault(inst_idx_fetch, {})[curr_cycle] = "WAIT"

        # ---------------- APPLY FLUSH IF MISPREDICTED ----------------
        if flush_pipeline:
            new_if_id = IF_ID_Register()  # Flush IF/ID
            new_id_ex = ID_EX_Register()  # Flush ID/EX
            self.pc = correct_target_pc

        # Update inter-stage pipeline registers
        self.mem_wb = new_mem_wb
        self.ex_mem = new_ex_mem
        if not stall_pipeline or flush_pipeline:
            self.id_ex = new_id_ex
            self.if_id = new_if_id

        # Record Cycle Snapshot for UI/CLI
        snapshot = CycleSnapshot(
            cycle=curr_cycle,
            if_inst=self.if_id.instruction.disassemble() if self.if_id.valid and self.if_id.instruction else "—",
            id_inst=self.id_ex.instruction.disassemble() if self.id_ex.valid and self.id_ex.instruction else "—",
            ex_inst=self.ex_mem.instruction.disassemble() if self.ex_mem.valid and self.ex_mem.instruction else "—",
            mem_inst=self.mem_wb.instruction.disassemble() if self.mem_wb.valid and self.mem_wb.instruction else "—",
            wb_inst=retired_inst_wb.disassemble() if retired_inst_wb else "—",
            stall=stall_pipeline,
            flush=flush_pipeline,
            forward_a=forward_a_src,
            forward_b=forward_b_src,
            pc=self.pc,
            note=note
        )
        self.snapshots.append(snapshot)

        # Check if pipeline has completely drained
        pipeline_empty = not (self.if_id.valid or self.id_ex.valid or self.ex_mem.valid or self.mem_wb.valid)
        if pipeline_empty and (self.pc // 4 >= len(program) or self.halted):
            self.halted = True
            return False

        return True

    def run(self, program: List[Instruction], max_cycles: int = 2000) -> int:
        """Runs the pipeline until halt or max cycles."""
        while not self.halted and self.cycle_count < max_cycles:
            if not self.clock_tick(program):
                break
        return self.cycle_count

    @property
    def cpi(self) -> float:
        """Cycles Per Instruction (CPI = Cycles / Retired Instructions)."""
        return (self.cycle_count / self.instructions_retired) if self.instructions_retired > 0 else 1.0

    @property
    def throughput_ipc(self) -> float:
        """Instructions Per Cycle (IPC = 1 / CPI)."""
        return 1.0 / self.cpi if self.cpi > 0 else 0.0

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "Total Cycles": self.cycle_count,
            "Instructions Retired": self.instructions_retired,
            "CPI (Cycles Per Instruction)": round(self.cpi, 3),
            "IPC (Throughput)": round(self.throughput_ipc, 3),
            "Stall Cycles": self.stall_cycles,
            "Flush Cycles (Branch Penalty)": self.flush_cycles,
            "Forwarding Events (EX & MEM)": self.forward_a_events + self.forward_b_events,
            "Branch Predictor Accuracy (%)": round(self.branch_predictor.accuracy * 100, 2),
            "Forwarding Enabled": self.enable_forwarding,
            "Predictor Mode": self.branch_predictor_mode.value,
        }
