
import time
import unittest

from timing.timing import Timing

# logging.basicConfig(level=logging.DEBUG)


class Tests(unittest.TestCase):

    @unittest.expectedFailure
    def test_timing(self):
        Timing('timing.name')
        # TimingCache.clear()
        self.fail()
