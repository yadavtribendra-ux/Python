"""
Memory Subsystem Module
=======================
Simulates main memory (RAM), Harvard / Princeton address segmentation,
Instruction Memory, Data Memory, and Memory-Mapped Transaction Buffers.

Course Outcome Mapping:
- CO1: Data representation and memory addressing modes.
- CO4: Memory hierarchy and memory organization.
"""

from typing import Dict, List, Any


class Memory:
    """
    Simulates a 32-bit word-addressable memory system.
    Segments:
      - 0x0000 - 0x0FFF : Instruction / Rule Code Segment
      - 0x1000 - 0x1FFF : Account Profile Data Segment (velocity stats, 30-day avg, limits)
      - 0x2000 - 0x20FF : Memory-Mapped Transaction Buffer (Incoming live transaction)
      - 0x3000 - 0x30FF : Fraud Decision Output Register (Risk score, decision code)
    """
    CODE_BASE_ADDR   = 0x0000
    DATA_BASE_ADDR   = 0x1000
    TXN_BUFFER_ADDR  = 0x2000
    DECISION_ADDR    = 0x3000

    # Offsets inside Transaction Buffer
    TXN_AMOUNT_OFF   = 0x00  # [0x2000]
    TXN_BALANCE_OFF  = 0x04  # [0x2004]
    TXN_VELOCITY_OFF = 0x08  # [0x2008]
    TXN_PIN_FAIL_OFF = 0x0C  # [0x200C]
    TXN_GEO_SPD_OFF  = 0x10  # [0x2010]
    TXN_MCC_OFF      = 0x14  # [0x2014]
    TXN_DEV_TRUST_OFF= 0x18  # [0x2018]
    TXN_HOUR_OFF     = 0x1C  # [0x201C]

    def __init__(self, size_bytes: int = 65536):
        self.size_bytes = size_bytes
        self.storage: Dict[int, int] = {}  # Word-aligned address -> 32-bit int
        self.access_count: int = 0
        self.read_count: int = 0
        self.write_count: int = 0

    def reset(self):
        self.storage.clear()
        self.access_count = 0
        self.read_count = 0
        self.write_count = 0

    def read_word(self, byte_addr: int) -> int:
        """Reads a 32-bit word from a 4-byte aligned memory address."""
        aligned_addr = byte_addr & ~0x3
        self.access_count += 1
        self.read_count += 1
        return self.storage.get(aligned_addr, 0)

    def write_word(self, byte_addr: int, value: int):
        """Writes a 32-bit word to a 4-byte aligned memory address."""
        aligned_addr = byte_addr & ~0x3
        self.access_count += 1
        self.write_count += 1
        self.storage[aligned_addr] = value & 0xFFFFFFFF

    def load_transaction_buffer(self, txn: Dict[str, Any]):
        """
        Loads incoming transaction fields into Memory-Mapped Transaction Buffer (0x2000).
        Allows CPU instructions to use 'LW' (Load Word) to fetch transaction features.
        """
        base = self.TXN_BUFFER_ADDR
        self.write_word(base + self.TXN_AMOUNT_OFF, int(txn.get("amount", 0)))
        self.write_word(base + self.TXN_BALANCE_OFF, int(txn.get("balance", 0)))
        self.write_word(base + self.TXN_VELOCITY_OFF, int(txn.get("frequency", 0)))
        self.write_word(base + self.TXN_PIN_FAIL_OFF, int(txn.get("failed_pins", 0)))
        self.write_word(base + self.TXN_GEO_SPD_OFF, int(txn.get("geo_speed", 0)))
        self.write_word(base + self.TXN_MCC_OFF, int(txn.get("mcc", 0)))
        dev_trust = 0 if txn.get("new_device", False) else 1
        self.write_word(base + self.TXN_DEV_TRUST_OFF, dev_trust)
        self.write_word(base + self.TXN_HOUR_OFF, int(txn.get("hour", 12)))

    def load_profile_data(self, profile: Dict[str, Any]):
        """Loads account baseline profile limits into Data Memory (0x1000)."""
        base = self.DATA_BASE_ADDR
        self.write_word(base + 0x00, int(profile.get("large_limit", 50000)))
        self.write_word(base + 0x04, int(profile.get("rapid_limit", 5)))
        self.write_word(base + 0x08, int(profile.get("pin_limit", 3)))
        self.write_word(base + 0x0C, int(profile.get("speed_limit", 800)))
        self.write_word(base + 0x10, int(profile.get("risk_limit", 4)))
