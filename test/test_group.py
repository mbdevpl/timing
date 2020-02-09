"""Tests of handling of group of timings."""

import contextlib
import logging
import time
import types
import unittest

from timing.group import TimingGroup
from timing.utils import get_timing_group, query_cache

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_basic(self):
        timers = TimingGroup('timings.basic')
        self.assertFalse(timers == 'timings.basic')
        other_timers = TimingGroup('timings.basic')
        self.assertEqual(timers, other_timers)
        self.assertEqual(timers.name, 'timings.basic')
        self.assertListEqual(timers.timings, [])
        self.assertEqual(timers.summary, {})
        timer = timers.start('timer')
        time.sleep(0.01)
        timer.stop()
        timer = timers.start('sub.timer')
        time.sleep(0.01)
        timer.stop()
        _LOG.info('%s', timers)
        _LOG.info('%r', timers)
        self.assertEqual(timers, timers)
        self.assertNotEqual(timers, other_timers)

    def test_measure_context(self):
        timers = TimingGroup('timings.contexts')

        with timers.measure('context1'):
            time.sleep(0.01)

        self.assertIn('context1', timers.summary)
        self.assertEqual(timers.summary['context1']['samples'], 1)

    def test_measure_decorator(self):
        timers = TimingGroup('timings.decorators')

        @timers.measure
        def add(num1, num2):
            time.sleep(0.02)
            return num1 + num2

        self.assertNotIsInstance(add, contextlib.ContextDecorator)
        self.assertIsInstance(add, types.FunctionType)

        @timers.measure('mult')
        def multiply(num1, num2):
            time.sleep(0.02)
            return num1 * num2

        self.assertNotIsInstance(multiply, contextlib.ContextDecorator)
        self.assertIsInstance(multiply, types.FunctionType)

        self.assertEqual(add(21, 21), 42)
        self.assertEqual(add(-5, 5), 0)
        self.assertEqual(multiply(21, 2), 42)
        self.assertEqual(multiply(-5, 5), -25)
        self.assertIn('add', timers.summary)
        self.assertEqual(timers.summary['add']['samples'], 2)
        self.assertNotIn('multiply', timers.summary)
        self.assertIn('mult', timers.summary)
        self.assertEqual(timers.summary['mult']['samples'], 2)

    def test_context_or_decorator(self):
        timers = TimingGroup('timings.context_or_decorator')

        def sub(num1, num2):
            time.sleep(0.001)
            return num1 - num2

        context = timers.measure('sub')
        self.assertIsInstance(context, contextlib.ContextDecorator)
        self.assertNotIsInstance(context, types.FunctionType)
        decorated = timers.measure(sub)
        self.assertNotIsInstance(decorated, contextlib.ContextDecorator)
        self.assertIsInstance(decorated, types.FunctionType)
        self.assertEqual(decorated(10, 11), -1)
        named_decorated = timers.measure(sub, 'sub')
        self.assertNotIsInstance(named_decorated, contextlib.ContextDecorator)
        self.assertIsInstance(named_decorated, types.FunctionType)
        self.assertEqual(named_decorated(100, 110), -10)

    def test_measure_many(self):
        timers = TimingGroup('timings.many')
        for _ in timers.measure_many('by_samples', samples=10):
            time.sleep(0.001)
        for _ in timers.measure_many('by_threshold', threshold=0.01):
            time.sleep(0.001)
        for _ in timers.measure_many('by_both', samples=10, threshold=0.01):
            time.sleep(0.001)
        self.assertGreaterEqual(len(timers.timings), 12)

    def test_query_cache(self):
        timers = get_timing_group('timings.root_group.subgroup')
        with timers.measure('context1'):
            time.sleep(0.01)

        root_timers = get_timing_group('timings.root_group')
        self.assertIs(timers, timers.query_cache())
        self.assertIs(timers, root_timers.query_cache('subgroup'))
        self.assertIs(timers, query_cache('timings.root_group.subgroup'))
        self.assertIs(timers, query_cache('timings.root_group', 'subgroup'))
        self.assertIs(timers, query_cache('timings', 'root_group', 'subgroup'))
