
import logging
import time
import unittest

from timing.timing import Timing

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_basic(self):
        timer = Timing('timing')
        self.assertNotEqual(timer, 'timing')
        other_timer = Timing('timing')
        self.assertEqual(timer, other_timer)
        self.assertEqual(timer.name, 'timing')
        self.assertIsNone(timer.begin)
        self.assertIsNone(timer.end)
        self.assertIsNone(timer.elapsed)
        timer.start()
        time.sleep(0.01)
        self.assertIsNotNone(timer.begin)
        timer.stop()
        self.assertIsNotNone(timer.end)
        self.assertGreater(timer.elapsed, 0)
        _LOG.info('%s', timer)
        _LOG.info('%r', timer)
        self.assertEqual(timer, timer)
        self.assertNotEqual(timer, other_timer)
