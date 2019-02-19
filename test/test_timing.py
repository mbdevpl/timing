
import logging
import os
import platform
from time import perf_counter as original_perf_counter
import time
import unittest
import unittest.mock

import numpy as np

from timing.timing import \
    TimingConfig, TimingCache, Timing, TimingGroup, \
    get_timing_group, query_cache, normalize_overhead

# logging.basicConfig(level=logging.DEBUG)


def slow_perf_counter():
    time.sleep(0.1)
    return original_perf_counter()


def erratic_perf_counter():
    time.sleep(np.random.uniform(0.0, 0.1))
    return original_perf_counter()


class Tests(unittest.TestCase):

    @unittest.expectedFailure
    def test_timing(self):
        Timing('timing.name')
        # TimingCache.clear()
        self.fail()

    @unittest.expectedFailure
    def test_timing_group(self):
        TimingGroup('timing.group.name')
        # TimingCache.clear()
        self.fail()

    @unittest.expectedFailure
    def test_get_timing_group(self):
        get_timing_group('timing.group.name')
        TimingCache.clear()
        self.fail()

    @unittest.expectedFailure
    def test_query_cache(self):
        query_cache('timing.group.name')
        self.fail()

    def test_overhead(self):
        self.assertTrue(TimingConfig.enable_cache)

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
            self.assertLessEqual(TimingConfig.overhead, 0.1)
        self.assertTrue(any(all(_ in line for _ in ('ERROR', 'variance', 'stdev', 'large'))
                            for line in log.output), msg=log.output)
        self.assertTrue(any(all(_ in line for _ in ('ERROR', 'mean', 'median', 'large'))
                            for line in log.output), msg=log.output)

        normalize_overhead()
        self.assertLessEqual(TimingConfig.overhead, 0.0001)

        self.assertTrue(not TimingCache.hierarchical, msg=TimingCache.hierarchical)
        self.assertTrue(not TimingCache.flat, msg=TimingCache.flat)
        self.assertTrue(not TimingCache.chronological, msg=TimingCache.chronological)
