"""Logging-like interface for timing the application.

First version written on 7 September 2016.

Copyright 2016, 2018  Mateusz Bysiek https://mbdevpl.github.io/
"""

# pylint: disable=too-few-public-methods

import collections
import logging
import statistics
import time
import typing as t

from .config import TimingConfig
from .group import TimingGroup
from .cache import TimingCache

if __debug__:
    _LOG = logging.getLogger(__name__)


class Timing:

    """Timing of performance-critical parts of application.

    Uses time.perf_counter(): https://docs.python.org/3/library/time.html#time.perf_counter
    """

    def __init__(self, name: str):
        assert isinstance(name, str)

        # self._group = None  # type: t.Optional[TimingGroup]
        self._name = name  # type: str
        self._begin = None  # type: float
        self._end = None  # type: float
        self._elapsed = None  # type: float

    def _calculate_elapsed(self):
        assert isinstance(self._begin, float)
        assert isinstance(self._end, float)

        self._elapsed = self._end - self._begin

    @property
    def name(self):
        return self._name

    @property
    def begin(self):
        return self._begin

    @property
    def end(self):
        return self._end

    @property
    def elapsed(self):
        return self._elapsed

    def start(self):
        """Start the timer."""
        self._begin = time.perf_counter()

    def stop(self):
        """Stop the timer."""
        self._end = time.perf_counter()
        self._calculate_elapsed()

    def __eq__(self, other):
        if not isinstance(other, Timing):
            return False
        return self._name == other.name and self._begin == other.begin \
            and self._end == other.end and self._elapsed == other.elapsed

    def __str__(self):
        args = [self._name, self._begin, self._end, self._elapsed]
        return '{}({})'.format(type(self).__name__, ', '.join([str(_) for _ in args]))

    def __repr__(self):
        return str(self)


def get_timing_group(name: str) -> TimingGroup:
    """Work similarily logging.get_logger()."""
    assert isinstance(name, str), type(name)
    if name in TimingCache.flat:
        return TimingCache.flat[name]

    name_fragments = name.split('.')

    if TimingConfig.enable_cache:
        timing_cache = TimingCache.hierarchical

        for i, name_fragment in enumerate(name_fragments):
            if name_fragment not in timing_cache:
                for level in range(i, len(name_fragments)):
                    timing_cache[name_fragments[level]] = collections.OrderedDict()
                    timing_cache = timing_cache[name_fragments[level]]
                break
            timing_cache = timing_cache[name_fragment]

    timing_group = TimingGroup(name)

    if TimingConfig.enable_cache:
        timing_cache['.'] = timing_group
        TimingCache.flat[name] = timing_group

    return timing_group


def query_cache(name: str) -> t.Union[dict, TimingGroup, Timing]:
    """Request timing data from global cache."""
    return TimingCache.query(name)


def normalize_overhead(samples: int = 10000, threshold: float = 1.0):
    """Investigate overhead of starting and stopping the timer.

    Do it so as to take the overhead into account when calculating actual execution times."""
    assert isinstance(samples, int)
    assert isinstance(threshold, float)

    timing_overhead = Timing('timing overhead test')
    overheads = []

    cache_status = TimingConfig.enable_cache
    TimingConfig.enable_cache = False
    __ = TimingGroup('timing_overhead_normalization')
    for _ in __.measure_many('overhead', samples=samples, threshold=threshold):
        timing_overhead.start()
        timing_overhead.stop()
        overheads.append(timing_overhead.elapsed)

    TimingConfig.enable_cache = cache_status

    mean = statistics.mean(overheads)
    median = statistics.median(overheads)
    stdev = statistics.pstdev(overheads, mean)
    variance = statistics.pvariance(overheads, mean)

    TimingConfig.overhead = median

    if __debug__:
        _LOG.log(
            logging.DEBUG if all(_ <= 0.00001 for _ in (mean, median, stdev, variance))
            else logging.WARNING,
            'normalized overhead using %i samples: mean=%f, median=%f, stdev=%f, variance=%f',
            samples, mean, median, stdev, variance)

        if stdev > 0.0001 or variance > 0.0001:
            _LOG.error(
                'stdev=%f and/or variance=%f are large -- timing results will not be stable',
                stdev, variance)

        if mean > 0.0001 or median > 0.0001:
            _LOG.error(
                'mean=%f and/or median=%f are large -- timing will incur overhead',
                mean, median)


normalize_overhead()
