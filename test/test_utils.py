
import logging
import os
import platform
from time import perf_counter as original_perf_counter
import time
import unittest
import unittest.mock

import numpy as np

from timing.config import TimingConfig
from timing.cache import TimingCache
from timing.utils import get_timing_group, query_cache, normalize_overhead


def slow_perf_counter():
    time.sleep(0.1)
    return original_perf_counter()


def erratic_perf_counter():
    time.sleep(np.random.uniform(0.0, 0.1))
    return original_perf_counter()


class Tests(unittest.TestCase):

    def test_get_timing_group(self):
        self.assertTrue(TimingConfig.enable_cache)
        TimingConfig.enable_cache = False

        timers = get_timing_group('timings.getting_group')
        self.assertIsNot(timers, get_timing_group('timings.getting_group'))

        TimingConfig.enable_cache = True

        timers = get_timing_group('timings.getting_group')
        self.assertIs(timers, get_timing_group('timings.getting_group'))
        self.assertIs(timers, get_timing_group('timings', 'getting_group'))
        with self.assertRaises(AssertionError):
            get_timing_group(32)

    def test_query_cache(self):
        with self.assertRaises(KeyError):
            query_cache('timings.non_existing_group')
        timers = get_timing_group('timings.existing_group')
        self.assertIs(timers, query_cache('timings.existing_group'))
        self.assertIs(timers, query_cache('timings', 'existing_group'))

    def test_overhead(self):
        self.assertTrue(TimingConfig.enable_cache)
        TimingCache.clear()

        normalize_overhead()
        self.assertLessEqual(TimingConfig.overhead, 0.0001)

        with self.assertLogs(level=logging.ERROR) as log:
            with unittest.mock.patch.object(time, 'perf_counter', new=slow_perf_counter):
                normalize_overhead()
            self.assertGreaterEqual(TimingConfig.overhead, 0.1)
        if platform.system() == 'Linux' or not os.environ.get('CI'):
            self.assertFalse(any(all(_ in line for _ in ('ERROR', 'variance', 'stdev', 'large'))
                                 for line in log.output), msg=log.output)
        self.assertTrue(any(all(_ in line for _ in ('ERROR', 'mean', 'median', 'large'))
                            for line in log.output), msg=log.output)

        with self.assertLogs(level=logging.ERROR) as log:
            with unittest.mock.patch.object(time, 'perf_counter', new=erratic_perf_counter):
                normalize_overhead()
            self.assertLessEqual(TimingConfig.overhead, 0.125)
        self.assertTrue(any(all(_ in line for _ in ('ERROR', 'variance', 'stdev', 'large'))
                            for line in log.output), msg=log.output)
        self.assertTrue(any(all(_ in line for _ in ('ERROR', 'mean', 'median', 'large'))
                            for line in log.output), msg=log.output)

        normalize_overhead()
        self.assertLessEqual(TimingConfig.overhead, 0.0001)

        self.assertTrue(not TimingCache.hierarchical, msg=TimingCache.hierarchical)
        self.assertTrue(not TimingCache.flat, msg=TimingCache.flat)
        self.assertTrue(not TimingCache.chronological, msg=TimingCache.chronological)
