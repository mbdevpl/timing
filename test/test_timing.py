
import time
import unittest

from timing.timing import Timing
from timing.group import TimingGroup

# logging.basicConfig(level=logging.DEBUG)


class Tests(unittest.TestCase):

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
