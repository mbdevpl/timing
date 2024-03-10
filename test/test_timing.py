"""Tests for the time measurement itself."""

import copy
import logging
import time
import unittest

from timing.timing import Timing, TimingState

_LOG = logging.getLogger(__name__)


class Tests(unittest.TestCase):

    def test_name(self):
        timer = Timing('timing')
        self.assertEqual(timer.name, 'timing')
        self.assertEqual(timer.state, TimingState.NOT_STARTED)
        with self.assertRaises(AssertionError):
            _LOG.debug('%f', timer.begin)
        with self.assertRaises(AssertionError):
            _LOG.debug('%f', timer.end)
        with self.assertRaises(AssertionError):
            _LOG.debug('%f', timer.elapsed)

    def test_start(self):
        timer = Timing('timing')
        timer.start()
        self.assertEqual(timer.state, TimingState.RUNNING)
        time.sleep(0.01)
        self.assertIsInstance(timer.begin, float)
        self.assertGreater(timer.begin, 0)
        with self.assertRaises(AssertionError):
            _LOG.debug('%f', timer.end)
        with self.assertRaises(AssertionError):
            _LOG.debug('%f', timer.elapsed)

    def test_stop(self):
        timer = Timing('timing')
        timer.start()
        time.sleep(0.01)
        timer.stop()
        self.assertEqual(timer.state, TimingState.FINISHED)
        self.assertIsInstance(timer.end, float)
        self.assertGreater(timer.end, 0)
        self.assertIsInstance(timer.elapsed, float)
        self.assertGreater(timer.elapsed, 0)

    def test_compare(self):
        timer = Timing('timing')
        other_timer = Timing('timing')
        self.assertEqual(timer, other_timer)
        # start
        timer.start()
        self.assertNotEqual(timer, other_timer)
        other_timer.start()
        self.assertEqual(timer.state, other_timer.state)
        self.assertNotEqual(timer, other_timer)
        other_timer = copy.deepcopy(timer)
        time.sleep(0.01)
        self.assertEqual(timer, other_timer)
        # stop
        timer.stop()
        self.assertNotEqual(timer, other_timer)
        other_timer.stop()
        self.assertEqual(timer.state, other_timer.state)
        self.assertNotEqual(timer, other_timer)
        other_timer = copy.deepcopy(timer)
        self.assertEqual(timer, other_timer)
