"""
Cache Memory Subsystem Module
=============================
Simulates hardware CPU cache with configurable associativity, block size,
replacement policies (LRU, FIFO, Random), write policies (Write-Through, Write-Back),
and quantitative AMAT (Average Memory Access Time) evaluation.

Course Outcome Mapping:
- CO4: Cache memory principles, mapping techniques (Direct, Set-Associative, Fully Associative),
  replacement policies, and quantitative memory hierarchy performance analysis.
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


class ReplacementPolicy(Enum):
    LRU = "LRU (Least Recently Used)"
    FIFO = "FIFO (First-In, First-Out)"
    RANDOM = "Random"


class WritePolicy(Enum):
    WRITE_THROUGH = "Write-Through"
    WRITE_BACK = "Write-Back"


class CacheType(Enum):
    INSTRUCTION = "I-Cache (Rule Microcode)"
    DATA = "D-Cache (Account Profiles & Features)"
    UNIFIED = "Unified Cache"


@dataclass
class CacheLine:
    valid: bool = False
    dirty: bool = False
    tag: int = 0
    data: List[int] = field(default_factory=list)  # Words stored in this line
    last_access_time: int = 0
    insertion_time: int = 0


@dataclass
class CacheSet:
    lines: List[CacheLine] = field(default_factory=list)


@dataclass
class CacheAccessResult:
    hit: bool
    address: int
    tag: int
    set_index: int
    block_offset: int
    miss_type: Optional[str] = None  # "compulsory", "capacity", "conflict"
    cycles_spent: int = 1
    evicted: bool = False
    evicted_dirty: bool = False


class Cache:
    """
    Hardware Cache Simulator.
    Calculates address bit fields:
      [ Tag (T bits) | Set Index (S bits) | Block Offset (B bits) | Byte Offset (2 bits) ]
    """
    def __init__(
        self,
        name: str = "L1-Cache",
        total_size_bytes: int = 1024,      # e.g. 1 KB
        block_size_bytes: int = 16,        # 16 bytes = 4 words
        associativity: int = 2,            # 2-way set-associative (1=Direct, total=Full)
        replacement_policy: ReplacementPolicy = ReplacementPolicy.LRU,
        write_policy: WritePolicy = WritePolicy.WRITE_BACK,
        hit_latency_cycles: int = 1,
        miss_penalty_cycles: int = 20,
    ):
        self.name = name
        self.total_size_bytes = total_size_bytes
        self.block_size_bytes = block_size_bytes
        self.words_per_block = max(1, block_size_bytes // 4)
        self.associativity = associativity
        self.replacement_policy = replacement_policy
        self.write_policy = write_policy
        self.hit_latency_cycles = hit_latency_cycles
        self.miss_penalty_cycles = miss_penalty_cycles

        # Hardware dimension calculations
        self.num_blocks = total_size_bytes // block_size_bytes
        if associativity >= self.num_blocks:
            self.num_sets = 1
            self.associativity = self.num_blocks
            self.is_fully_associative = True
        else:
            self.num_sets = max(1, self.num_blocks // associativity)
            self.is_fully_associative = False

        self.byte_offset_bits = 2  # 32-bit word = 4 bytes
        self.block_offset_bits = int(math.log2(self.words_per_block)) if self.words_per_block > 1 else 0
        self.index_bits = int(math.log2(self.num_sets)) if self.num_sets > 1 else 0
        self.tag_bits = 32 - (self.index_bits + self.block_offset_bits + self.byte_offset_bits)

        # Allocate cache sets
        self.sets: List[CacheSet] = []
        for _ in range(self.num_sets):
            lines = [CacheLine(data=[0] * self.words_per_block) for _ in range(self.associativity)]
            self.sets.append(CacheSet(lines=lines))

        # Statistics & 3C Miss tracking
        self.timer: int = 0
        self.total_accesses: int = 0
        self.hits: int = 0
        self.misses: int = 0
        self.reads: int = 0
        self.writes: int = 0
        self.compulsory_misses: int = 0
        self.conflict_misses: int = 0
        self.capacity_misses: int = 0
        self.writebacks: int = 0
        self.seen_blocks: set = set()

    def reset(self):
        """Clear cache state and counters."""
        self.sets = []
        for _ in range(self.num_sets):
            lines = [CacheLine(data=[0] * self.words_per_block) for _ in range(self.associativity)]
            self.sets.append(CacheSet(lines=lines))
        self.timer = 0
        self.total_accesses = 0
        self.hits = 0
        self.misses = 0
        self.reads = 0
        self.writes = 0
        self.compulsory_misses = 0
        self.conflict_misses = 0
        self.capacity_misses = 0
        self.writebacks = 0
        self.seen_blocks.clear()

    def decode_address(self, byte_addr: int) -> Tuple[int, int, int]:
        """
        Splits 32-bit byte address into: (tag, set_index, word_offset)
        """
        word_addr = (byte_addr >> 2)
        word_offset = word_addr & ((1 << self.block_offset_bits) - 1) if self.block_offset_bits > 0 else 0
        set_index = (word_addr >> self.block_offset_bits) & ((1 << self.index_bits) - 1) if self.index_bits > 0 else 0
        tag = word_addr >> (self.block_offset_bits + self.index_bits)
        return tag, set_index, word_offset

    def access(self, byte_addr: int, is_write: bool = False, write_data: int = 0) -> CacheAccessResult:
        """
        Simulates an atomic cache read or write access.
        Returns detailed CacheAccessResult for pipeline and UI visualization.
        """
        self.timer += 1
        self.total_accesses += 1
        if is_write:
            self.writes += 1
        else:
            self.reads += 1

        tag, set_index, word_offset = self.decode_address(byte_addr)
        block_address = byte_addr >> (self.block_offset_bits + 2)
        cache_set = self.sets[set_index]

        # 1. Search for Tag in Set (Parallel comparison in hardware)
        hit_line = None
        for line in cache_set.lines:
            if line.valid and line.tag == tag:
                hit_line = line
                break

        if hit_line is not None:
            # CACHE HIT!
            self.hits += 1
            hit_line.last_access_time = self.timer
            if is_write:
                hit_line.data[word_offset] = write_data
                if self.write_policy == WritePolicy.WRITE_BACK:
                    hit_line.dirty = True
                else:
                    self.writebacks += 1  # Write directly through to main memory

            return CacheAccessResult(
                hit=True,
                address=byte_addr,
                tag=tag,
                set_index=set_index,
                block_offset=word_offset,
                cycles_spent=self.hit_latency_cycles,
            )

        # CACHE MISS!
        self.misses += 1
        # Classify 3C Miss:
        miss_type = "compulsory"
        if block_address not in self.seen_blocks:
            self.compulsory_misses += 1
            self.seen_blocks.add(block_address)
        else:
            # If all sets combined have capacity left, it's a conflict miss; else capacity
            total_valid_lines = sum(1 for s in self.sets for ln in s.lines if ln.valid)
            if total_valid_lines >= self.num_blocks:
                self.capacity_misses += 1
                miss_type = "capacity"
            else:
                self.conflict_misses += 1
                miss_type = "conflict"

        # 2. Find Victim Line for Replacement
        victim_line, evicted, evicted_dirty = self._select_victim(cache_set)
        if evicted_dirty:
            self.writebacks += 1

        # 3. Fill Line with newly fetched block
        victim_line.valid = True
        victim_line.tag = tag
        victim_line.last_access_time = self.timer
        victim_line.insertion_time = self.timer
        victim_line.data = [0] * self.words_per_block

        if is_write:
            victim_line.data[word_offset] = write_data
            victim_line.dirty = (self.write_policy == WritePolicy.WRITE_BACK)
        else:
            victim_line.dirty = False

        total_penalty = self.hit_latency_cycles + self.miss_penalty_cycles
        if evicted_dirty:
            total_penalty += self.miss_penalty_cycles // 2  # Extra penalty to write back dirty line

        return CacheAccessResult(
            hit=False,
            address=byte_addr,
            tag=tag,
            set_index=set_index,
            block_offset=word_offset,
            miss_type=miss_type,
            cycles_spent=total_penalty,
            evicted=evicted,
            evicted_dirty=evicted_dirty
        )

    def _select_victim(self, cache_set: CacheSet) -> Tuple[CacheLine, bool, bool]:
        """Selects line for replacement based on configured policy (LRU / FIFO / Random)."""
        # Check for invalid line first (no eviction required)
        for line in cache_set.lines:
            if not line.valid:
                return line, False, False

        # Eviction needed
        evicted_dirty = False
        if self.replacement_policy == ReplacementPolicy.LRU:
            victim = min(cache_set.lines, key=lambda ln: ln.last_access_time)
        elif self.replacement_policy == ReplacementPolicy.FIFO:
            victim = min(cache_set.lines, key=lambda ln: ln.insertion_time)
        else:  # RANDOM
            victim = random.choice(cache_set.lines)

        evicted_dirty = victim.dirty
        return victim, True, evicted_dirty

    @property
    def hit_rate(self) -> float:
        return (self.hits / self.total_accesses) if self.total_accesses > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        return (self.misses / self.total_accesses) if self.total_accesses > 0 else 0.0

    @property
    def amat(self) -> float:
        """
        Average Memory Access Time (AMAT):
        AMAT = Hit Time + (Miss Rate * Miss Penalty)
        """
        return self.hit_latency_cycles + (self.miss_rate * self.miss_penalty_cycles)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "Name": self.name,
            "Total Size (Bytes)": self.total_size_bytes,
            "Block Size (Bytes)": self.block_size_bytes,
            "Associativity": f"{self.associativity}-Way",
            "Num Sets": self.num_sets,
            "Tag Bits": self.tag_bits,
            "Index Bits": self.index_bits,
            "Offset Bits": self.block_offset_bits,
            "Total Accesses": self.total_accesses,
            "Hits": self.hits,
            "Misses": self.misses,
            "Hit Rate (%)": round(self.hit_rate * 100, 2),
            "Miss Rate (%)": round(self.miss_rate * 100, 2),
            "AMAT (Cycles)": round(self.amat, 3),
            "Compulsory Misses": self.compulsory_misses,
            "Conflict Misses": self.conflict_misses,
            "Capacity Misses": self.capacity_misses,
            "Writebacks": self.writebacks,
        }
