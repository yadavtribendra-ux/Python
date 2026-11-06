"""
Digital Logic Building Blocks & Gate Primitives
==============================================
Simulates combinational logic gates, multiplexers, decoders, full adders,
and condition bitmask evaluators for banking fraud rule processors.

Course Outcome Mapping:
- CO2: Arithmetic and Logic Unit (ALU) design, logic circuits, and arithmetic algorithms.
"""

from typing import Tuple, List, Dict


class LogicGates:
    """Primitive digital logic gates with delay and boolean operation modeling."""

    @staticmethod
    def gate_and(a: int, b: int) -> int:
        return 1 if (a and b) else 0

    @staticmethod
    def gate_or(a: int, b: int) -> int:
        return 1 if (a or b) else 0

    @staticmethod
    def gate_not(a: int) -> int:
        return 0 if a else 1

    @staticmethod
    def gate_xor(a: int, b: int) -> int:
        return 1 if (bool(a) ^ bool(b)) else 0

    @staticmethod
    def gate_nand(a: int, b: int) -> int:
        return 0 if (a and b) else 1

    @staticmethod
    def gate_nor(a: int, b: int) -> int:
        return 0 if (a or b) else 1

    @staticmethod
    def mux_2to1(d0: int, d1: int, sel: int) -> int:
        """2-to-1 Multiplexer: Output d1 if sel==1 else d0."""
        return d1 if sel else d0

    @staticmethod
    def mux_4to1(d0: int, d1: int, d2: int, d3: int, s0: int, s1: int) -> int:
        """4-to-1 Multiplexer using hierarchical 2:1 muxes."""
        m_low = LogicGates.mux_2to1(d0, d1, s0)
        m_high = LogicGates.mux_2to1(d2, d3, s0)
        return LogicGates.mux_2to1(m_low, m_high, s1)

    @staticmethod
    def decoder_2to4(s0: int, s1: int, enable: int = 1) -> Tuple[int, int, int, int]:
        """2-to-4 Active-High Decoder."""
        if not enable:
            return (0, 0, 0, 0)
        not_s0 = LogicGates.gate_not(s0)
        not_s1 = LogicGates.gate_not(s1)
        y0 = LogicGates.gate_and(not_s1, not_s0)
        y1 = LogicGates.gate_and(not_s1, s0)
        y2 = LogicGates.gate_and(s1, not_s0)
        y3 = LogicGates.gate_and(s1, s0)
        return (y0, y1, y2, y3)

    @staticmethod
    def full_adder_1bit(a: int, b: int, cin: int) -> Tuple[int, int]:
        """
        1-Bit Full Adder:
        Sum = a XOR b XOR cin
        Cout = (a AND b) OR (cin AND (a XOR b))
        """
        axorb = LogicGates.gate_xor(a, b)
        s = LogicGates.gate_xor(axorb, cin)
        cout = LogicGates.gate_or(
            LogicGates.gate_and(a, b),
            LogicGates.gate_and(cin, axorb)
        )
        return s, cout

    @staticmethod
    def comparator_32bit(a: int, b: int) -> Tuple[bool, bool, bool]:
        """
        32-bit Magnitude Comparator:
        Returns: (Equal, Greater, Less)
        """
        eq = (a == b)
        gt = (a > b)
        lt = (a < b)
        return eq, gt, lt


class FraudBitmaskLogic:
    """
    Dedicated hardware status register logic for fraud rule status.
    In banking hardware accelerators, fraud flags are encoded as bitmasks
    in a dedicated 32-bit Status / Fraud Register (FRAUD_FLAGS).
    """
    BIT_LARGE_AMOUNT     = 0  # 1 << 0 (1)
    BIT_VELOCITY_SPIKE   = 1  # 1 << 1 (2)
    BIT_GEO_IMPOSSIBLE   = 2  # 1 << 2 (4)
    BIT_AUTH_FAILURE     = 3  # 1 << 3 (8)
    BIT_DEVICE_UNTRUSTED = 4  # 1 << 4 (16)
    BIT_BALANCE_DEFICIT  = 5  # 1 << 5 (32)
    BIT_HIGH_RISK_MCC    = 6  # 1 << 6 (64)
    BIT_OFF_HOURS        = 7  # 1 << 7 (128)

    RULE_DESCRIPTIONS: Dict[int, str] = {
        0: "Large Transaction Outlier (> Limit)",
        1: "Velocity Spike (> 5 txns in 10 mins)",
        2: "Impossible Geo-Velocity (> 800 km/h)",
        3: "Excessive Failed PIN/Auth Attempts",
        4: "Unrecognized / Blacklisted Device",
        5: "Insufficient Account Balance Deficit",
        6: "High-Risk Merchant Category Code (MCC)",
        7: "Anomalous Off-Hours Transaction (01:00-04:00)",
    }

    @classmethod
    def set_flag(cls, mask: int, bit_index: int, condition: bool) -> int:
        """Sets or clears a bit in the fraud status mask."""
        if condition:
            return mask | (1 << bit_index)
        return mask & ~(1 << bit_index)

    @classmethod
    def test_flag(cls, mask: int, bit_index: int) -> bool:
        """Tests whether a specific fraud flag bit is asserted."""
        return bool(mask & (1 << bit_index))

    @classmethod
    def decode_mask(cls, mask: int) -> List[str]:
        """Returns list of active triggered fraud rule names."""
        triggered = []
        for bit, desc in cls.RULE_DESCRIPTIONS.items():
            if mask & (1 << bit):
                triggered.append(desc)
        return triggered

    @classmethod
    def calculate_hardware_risk_score(cls, mask: int, weights: Dict[int, int] = None) -> int:
        """
        Hardware combinational risk score calculation:
        Computes weighted sum of asserted bits in parallel.
        """
        if weights is None:
            # Default risk weights per bit
            weights = {
                cls.BIT_LARGE_AMOUNT: 2,
                cls.BIT_VELOCITY_SPIKE: 2,
                cls.BIT_GEO_IMPOSSIBLE: 4,
                cls.BIT_AUTH_FAILURE: 3,
                cls.BIT_DEVICE_UNTRUSTED: 2,
                cls.BIT_BALANCE_DEFICIT: 3,
                cls.BIT_HIGH_RISK_MCC: 2,
                cls.BIT_OFF_HOURS: 1,
            }
        score = 0
        for bit, weight in weights.items():
            if mask & (1 << bit):
                score += weight
        return score
