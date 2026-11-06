"""
ISA (Instruction Set Architecture) Module for Bank Fraud Processor: RISC-F
========================================================================
Defines the instruction set, opcodes, register conventions, instruction word
formats (R, I, S, B, J), binary encoding/decoding, and assembly parser.

Course Outcome Mapping:
- CO1: Fundamentals of computer systems, data representation, instruction formats.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any


class Opcode(Enum):
    # R-Type: Arithmetic / Logical / Bitwise
    NOP     = (0x00, "R", "No Operation")
    ADD     = (0x01, "R", "Add: Rd = Rs1 + Rs2")
    SUB     = (0x02, "R", "Subtract: Rd = Rs1 - Rs2")
    AND     = (0x03, "R", "Bitwise AND: Rd = Rs1 & Rs2")
    OR      = (0x04, "R", "Bitwise OR: Rd = Rs1 | Rs2")
    XOR     = (0x05, "R", "Bitwise XOR: Rd = Rs1 ^ Rs2")
    SLL     = (0x06, "R", "Shift Left Logical: Rd = Rs1 << shamt")
    SRL     = (0x07, "R", "Shift Right Logical: Rd = Rs1 >> shamt")
    SLT     = (0x08, "R", "Set on Less Than: Rd = 1 if Rs1 < Rs2 else 0")
    SEQ     = (0x09, "R", "Set on Equal: Rd = 1 if Rs1 == Rs2 else 0")
    ABS_DIFF= (0x0A, "R", "Absolute Difference: Rd = |Rs1 - Rs2|")
    
    # I-Type: Immediate Arithmetic / Logic / Comparison / Memory
    ADDI    = (0x10, "I", "Add Immediate: Rd = Rs1 + Imm")
    SUBI    = (0x11, "I", "Subtract Immediate: Rd = Rs1 - Imm")
    ANDI    = (0x12, "I", "AND Immediate: Rd = Rs1 & Imm")
    ORI     = (0x13, "I", "OR Immediate: Rd = Rs1 | Imm")
    XORI    = (0x14, "I", "XOR Immediate: Rd = Rs1 ^ Imm")
    CMP_GT  = (0x15, "I", "Compare Greater Than: Rd = 1 if Rs1 > Imm else 0")
    CMP_GE  = (0x16, "I", "Compare Greater/Equal: Rd = 1 if Rs1 >= Imm else 0")
    CMP_LT  = (0x17, "I", "Compare Less Than: Rd = 1 if Rs1 < Imm else 0")
    CMP_EQ  = (0x18, "I", "Compare Equal: Rd = 1 if Rs1 == Imm else 0")
    LW      = (0x19, "I", "Load Word: Rd = Mem[Rs1 + Imm]")
    
    # S-Type: Memory Store
    SW      = (0x20, "S", "Store Word: Mem[Rs1 + Imm] = Rs2")
    
    # B-Type: Conditional Branches
    BEQ     = (0x28, "B", "Branch if Equal: if Rs1 == Rs2 goto Target")
    BNE     = (0x29, "B", "Branch if Not Equal: if Rs1 != Rs2 goto Target")
    BGT     = (0x2A, "B", "Branch if Greater: if Rs1 > Rs2 goto Target")
    BLT     = (0x2B, "B", "Branch if Less: if Rs1 < Rs2 goto Target")
    BGE     = (0x2C, "B", "Branch if Greater/Equal: if Rs1 >= Rs2 goto Target")
    
    # J-Type: Unconditional Jump / Flow
    JMP     = (0x30, "J", "Unconditional Jump: PC = Target")
    HALT    = (0x3F, "J", "Halt Processor Execution")

    @property
    def code(self) -> int:
        return self.value[0]

    @property
    def format_type(self) -> str:
        return self.value[1]

    @property
    def description(self) -> str:
        return self.value[2]


# Register ABI & Aliases for Fraud Rule Engine
# R0: Hardwired Zero
# R1: Txn Amount
# R2: Account Balance
# R3: Txn Velocity (recent count)
# R4: Failed PIN attempts
# R5: Geo-distance / speed (km/h)
# R6: Merchant Category Code (MCC)
# R7: Device Trust Flag (1=Trusted, 0=New/Suspicious)
# R8: Risk Score Accumulator
# R9: Fraud Flag Bitmask
# R10-R15: Temporary / ALU working registers
# R16-R23: Rule Threshold Profile Registers
# R24-R31: General purpose / scratchpad
REGISTER_ALIASES: Dict[str, int] = {
    "R0": 0, "ZERO": 0,
    "R1": 1, "AMT": 1,
    "R2": 2, "BAL": 2,
    "R3": 3, "VEL": 3,
    "R4": 4, "PIN_FAIL": 4,
    "R5": 5, "GEO_SPD": 5,
    "R6": 6, "MCC": 6,
    "R7": 7, "DEV_OK": 7,
    "R8": 8, "RISK_SCORE": 8,
    "R9": 9, "FRAUD_MASK": 9,
}
for i in range(32):
    REGISTER_ALIASES[f"R{i}"] = i
    REGISTER_ALIASES[f"r{i}"] = i


@dataclass
class Instruction:
    """Represents a single RISC-F instruction."""
    opcode: Opcode
    rd: int = 0
    rs1: int = 0
    rs2: int = 0
    imm: int = 0
    shamt: int = 0
    label: str = ""
    target_label: str = ""
    comment: str = ""
    source_line: str = ""
    address: int = 0  # Byte address in instruction memory

    def encode(self) -> int:
        """Encode the instruction into a 32-bit unsigned binary word."""
        fmt = self.opcode.format_type
        op = self.opcode.code & 0x3F  # 6 bits
        rd = self.rd & 0x1F          # 5 bits
        rs1 = self.rs1 & 0x1F        # 5 bits
        rs2 = self.rs2 & 0x1F        # 5 bits
        shamt = self.shamt & 0x1F    # 5 bits
        imm16 = self.imm & 0xFFFF    # 16 bits
        target26 = self.imm & 0x03FFFFFF  # 26 bits for J-type

        if fmt == "R":
            # [Op:6][Rd:5][Rs1:5][Rs2:5][Shamt:5][Funct:6] -> Funct unused, pad with 0
            return (op << 26) | (rd << 21) | (rs1 << 16) | (rs2 << 11) | (shamt << 6)
        elif fmt in ("I", "B", "S"):
            # [Op:6][Rd/Rs2:5][Rs1:5][Imm:16]
            return (op << 26) | (rd << 21) | (rs1 << 16) | imm16
        elif fmt == "J":
            # [Op:6][Target:26]
            return (op << 26) | target26
        return 0

    @staticmethod
    def decode(word: int, address: int = 0) -> "Instruction":
        """Decode a 32-bit binary word into an Instruction object."""
        op_code = (word >> 26) & 0x3F
        matched_op = None
        for op in Opcode:
            if op.code == op_code:
                matched_op = op
                break
        if not matched_op:
            matched_op = Opcode.NOP

        fmt = matched_op.format_type
        if fmt == "R":
            rd = (word >> 21) & 0x1F
            rs1 = (word >> 16) & 0x1F
            rs2 = (word >> 11) & 0x1F
            shamt = (word >> 6) & 0x1F
            return Instruction(matched_op, rd=rd, rs1=rs1, rs2=rs2, shamt=shamt, address=address)
        elif fmt in ("I", "B", "S"):
            rd = (word >> 21) & 0x1F
            rs1 = (word >> 16) & 0x1F
            imm = word & 0xFFFF
            # Sign extend 16-bit immediate
            if imm & 0x8000:
                imm -= 0x10000
            return Instruction(matched_op, rd=rd, rs1=rs1, imm=imm, address=address)
        elif fmt == "J":
            imm = word & 0x03FFFFFF
            return Instruction(matched_op, imm=imm, address=address)
        return Instruction(Opcode.NOP, address=address)

    def disassemble(self) -> str:
        """Human-readable assembly string."""
        op_name = self.opcode.name
        fmt = self.opcode.format_type
        if self.opcode == Opcode.NOP:
            return "NOP"
        if self.opcode == Opcode.HALT:
            return "HALT"

        if fmt == "R":
            if self.opcode in (Opcode.SLL, Opcode.SRL):
                return f"{op_name:<8} R{self.rd}, R{self.rs1}, {self.shamt}"
            return f"{op_name:<8} R{self.rd}, R{self.rs1}, R{self.rs2}"
        elif fmt == "I":
            if self.opcode == Opcode.LW:
                return f"{op_name:<8} R{self.rd}, {self.imm}(R{self.rs1})"
            return f"{op_name:<8} R{self.rd}, R{self.rs1}, #{self.imm}"
        elif fmt == "S":
            return f"{op_name:<8} R{self.rs2}, {self.imm}(R{self.rs1})"
        elif fmt == "B":
            target = self.target_label or f"#{self.imm}"
            return f"{op_name:<8} R{self.rs1}, R{self.rs2}, {target}"
        elif fmt == "J":
            target = self.target_label or f"#{self.imm}"
            return f"{op_name:<8} {target}"
        return f"{op_name}"

    def __repr__(self) -> str:
        return f"[{self.address:04X}] {self.disassemble()}"


def parse_register(tok: str) -> int:
    """Parse register name like R1, AMT, r5."""
    clean = tok.strip().rstrip(",").upper()
    if clean in REGISTER_ALIASES:
        return REGISTER_ALIASES[clean]
    if clean.startswith("R") and clean[1:].isdigit():
        return int(clean[1:])
    raise ValueError(f"Unknown register: {tok}")


def parse_assembly(source_code: str) -> List[Instruction]:
    """
    Parses a multi-line RISC-F assembly string into a list of Instruction objects.
    Resolves branch and jump labels to memory addresses (4 bytes per instruction).
    """
    lines = source_code.strip().splitlines()
    instructions: List[Instruction] = []
    labels: Dict[str, int] = {}
    cleaned_lines: List[Tuple[int, Optional[str], str, str]] = []  # (addr, label, code, comment)

    curr_addr = 0
    # Pass 1: Collect labels and clean instructions
    for line in lines:
        line = line.strip()
        if not line or line.startswith(";") or line.startswith("//"):
            continue

        comment = ""
        if ";" in line:
            line, comment = line.split(";", 1)
        elif "//" in line:
            line, comment = line.split("//", 1)
        line = line.strip()
        comment = comment.strip()

        lbl = None
        if ":" in line:
            lbl_part, rest = line.split(":", 1)
            lbl = lbl_part.strip()
            labels[lbl] = curr_addr
            line = rest.strip()

        if not line:
            continue

        cleaned_lines.append((curr_addr, lbl, line, comment))
        curr_addr += 4

    # Pass 2: Parse opcodes and operands, resolve labels
    for addr, lbl, code, comment in cleaned_lines:
        tokens = [t.strip().rstrip(",") for t in code.split() if t.strip()]
        if not tokens:
            continue
        op_str = tokens[0].upper()
        if not hasattr(Opcode, op_str):
            raise ValueError(f"Unknown opcode '{op_str}' at line: {code}")

        opcode = getattr(Opcode, op_str)
        fmt = opcode.format_type
        inst = Instruction(opcode=opcode, address=addr, comment=comment, source_line=code)

        if opcode in (Opcode.NOP, Opcode.HALT):
            pass
        elif fmt == "R":
            # R-type: OP rd, rs1, rs2 (or OP rd, rs1, shamt for shift)
            inst.rd = parse_register(tokens[1])
            inst.rs1 = parse_register(tokens[2])
            if opcode in (Opcode.SLL, Opcode.SRL):
                inst.shamt = int(tokens[3].lstrip("#"))
            else:
                inst.rs2 = parse_register(tokens[3])
        elif fmt == "I":
            if opcode == Opcode.LW:
                # LW rd, offset(rs1)
                inst.rd = parse_register(tokens[1])
                mem_part = tokens[2]
                if "(" in mem_part and mem_part.endswith(")"):
                    off_str, rs1_str = mem_part.split("(", 1)
                    inst.imm = int(off_str) if off_str else 0
                    inst.rs1 = parse_register(rs1_str.rstrip(")"))
                else:
                    inst.imm = int(mem_part.lstrip("#"))
            else:
                # OP rd, rs1, imm
                inst.rd = parse_register(tokens[1])
                inst.rs1 = parse_register(tokens[2])
                inst.imm = int(tokens[3].lstrip("#"))
        elif fmt == "S":
            # SW rs2, offset(rs1)
            inst.rs2 = parse_register(tokens[1])
            mem_part = tokens[2]
            if "(" in mem_part and mem_part.endswith(")"):
                off_str, rs1_str = mem_part.split("(", 1)
                inst.imm = int(off_str) if off_str else 0
                inst.rs1 = parse_register(rs1_str.rstrip(")"))
            else:
                inst.imm = int(mem_part.lstrip("#"))
        elif fmt == "B":
            # OP rs1, rs2, label
            inst.rs1 = parse_register(tokens[1])
            inst.rs2 = parse_register(tokens[2])
            target_str = tokens[3]
            inst.target_label = target_str
            if target_str in labels:
                target_addr = labels[target_str]
                # Branch offset relative to current instruction address
                inst.imm = (target_addr - addr) // 4
            else:
                inst.imm = int(target_str.lstrip("#"))
        elif fmt == "J":
            # JMP label / target
            target_str = tokens[1]
            inst.target_label = target_str
            if target_str in labels:
                inst.imm = labels[target_str]
            else:
                inst.imm = int(target_str.lstrip("#"))

        instructions.append(inst)

    return instructions
