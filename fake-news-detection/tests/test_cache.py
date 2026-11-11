"""
Unit Tests for Cache Subsystem Module (CO4)
"""

import unittest
from bank_fraud_simulator.cache import Cache, ReplacementPolicy, WritePolicy


class TestCacheSubsystem(unittest.TestCase):
    def test_cache_direct_mapped(self):
        # 64 bytes total, 16 bytes/block -> 4 blocks, 1-way (direct-mapped) -> 4 sets
        cache = Cache("L1-Direct", total_size_bytes=64, block_size_bytes=16, associativity=1)
        self.assertEqual(cache.num_sets, 4)
        self.assertEqual(cache.words_per_block, 4)

        # First access to address 0 -> Compulsory miss
        res1 = cache.access(0x0000, is_write=False)
        self.assertFalse(res1.hit)
        self.assertEqual(res1.miss_type, "compulsory")
        self.assertEqual(cache.misses, 1)

        # Second access to same block (offset 4) -> Hit
        res2 = cache.access(0x0004, is_write=False)
        self.assertTrue(res2.hit)
        self.assertEqual(cache.hits, 1)
        self.assertEqual(cache.hit_rate, 0.5)

    def test_cache_lru_eviction(self):
        # 32 bytes total, 16 bytes/block -> 2 blocks. 2-way associative -> 1 set with 2 lines
        cache = Cache("L1-LRU", total_size_bytes=32, block_size_bytes=16, associativity=2,
                      replacement_policy=ReplacementPolicy.LRU)

        # Access block 0 (address 0) -> Miss
        cache.access(0x0000)
        # Access block 1 (address 16) -> Miss
        cache.access(0x0010)
        # Re-access block 0 -> Hit (updates last access time)
        res_hit = cache.access(0x0000)
        self.assertTrue(res_hit.hit)

        # Access block 2 (address 32) -> Must evict LRU (which is block 1, since block 0 was re-accessed)
        res_evict = cache.access(0x0020)
        self.assertFalse(res_evict.hit)
        self.assertTrue(res_evict.evicted)

        # Block 0 should still hit!
        self.assertTrue(cache.access(0x0000).hit)

    def test_amat_calculation(self):
        cache = Cache("L1-Test", total_size_bytes=128, block_size_bytes=16, associativity=2,
                      hit_latency_cycles=1, miss_penalty_cycles=20)
        # 1 miss + 3 hits -> 75% hit rate, 25% miss rate
        cache.access(0x0000)  # Miss
        cache.access(0x0000)  # Hit
        cache.access(0x0004)  # Hit
        cache.access(0x0008)  # Hit

        self.assertEqual(cache.hit_rate, 0.75)
        self.assertEqual(cache.miss_rate, 0.25)
        # AMAT = 1 + (0.25 * 20) = 1 + 5 = 6.0 cycles
        self.assertAlmostEqual(cache.amat, 6.0, places=3)


if __name__ == "__main__":
    unittest.main()

