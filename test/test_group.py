
import time
import unittest

from timing.group import TimingGroup


class Tests(unittest.TestCase):

    @unittest.expectedFailure
    def test_timing_group(self):
        TimingGroup('timing.group.name')
        # TimingCache.clear()
        self.fail()

    def test_measure_context(self):
        timers = TimingGroup('timings.contexts')

        with timers.measure('context1'):
            time.sleep(0.01)

        self.assertIn('context1', timers.summary)
        self.assertEqual(timers.summary['context1']['samples'], 1)

    def test_measure_decorator(self):
        timers = TimingGroup('timings.decorators')

        @timers.measure
        def add(a, b):
            time.sleep(0.02)
            return a + b

        @timers.measure('mult')
        def multiply(a, b):
            time.sleep(0.02)
            return a * b

        self.assertEqual(add(21, 21), 42)
        self.assertEqual(add(-5, 5), 0)
        self.assertEqual(multiply(21, 2), 42)
        self.assertEqual(multiply(-5, 5), -25)
        self.assertIn('add', timers.summary)
        self.assertEqual(timers.summary['add']['samples'], 2)
        self.assertNotIn('multiply', timers.summary)
        self.assertIn('mult', timers.summary)
        self.assertEqual(timers.summary['mult']['samples'], 2)
