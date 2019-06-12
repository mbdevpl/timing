
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

    @unittest.expectedFailure
    def test_get_timing_group(self):
        get_timing_group('timing.group.name')
        TimingCache.clear()
        self.fail()

    @unittest.expectedFailure
    def test_query_cache(self):
        query_cache('timing.group.name')
        self.fail()

    @unittest.expectedFailure
    def test_timing(self):
        Timing('timing.name')
        # TimingCache.clear()
        self.fail()


class TimingGroupTests(unittest.TestCase):

    @unittest.expectedFailure
    def test_timing_group(self):
        TimingGroup('timing.group.name')
        # TimingCache.clear()
        self.fail()

    def test_measure_context(self):
        _time = TimingGroup('timings.contexts')

        with _time.measure('context1'):
            time.sleep(0.01)

        self.assertIn('context1', _time.summary)
        self.assertEqual(_time.summary['context1']['samples'], 1)

    def test_measure_decorator(self):
        _time = TimingGroup('timings.decorators')

        @_time.measure
        def add(a, b):
            time.sleep(0.02)
            return a + b

        @_time.measure('mult')
        def multiply(a, b):
            time.sleep(0.02)
            return a * b

        self.assertEqual(add(21, 21), 42)
        self.assertEqual(add(-5, 5), 0)
        self.assertEqual(multiply(21, 2), 42)
        self.assertEqual(multiply(-5, 5), -25)
        self.assertIn('add', _time.summary)
        self.assertEqual(_time.summary['add']['samples'], 2)
        self.assertNotIn('multiply', _time.summary)
        self.assertIn('mult', _time.summary)
        self.assertEqual(_time.summary['mult']['samples'], 2)
