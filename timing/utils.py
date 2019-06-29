"""Utility and supporting functions for timing module."""

import collections
import logging
import statistics
import typing as t

from .config import TimingConfig
from .timing import Timing
from .group import TimingGroup
from .cache import TimingCache

if __debug__:
    _LOG = logging.getLogger(__name__)


def get_timing_group(*name_fragments: t.Sequence[str]) -> TimingGroup:
    """Work similarily logging.getLogger()."""
    assert name_fragments
    assert all(isinstance(_, str) and _ for _ in name_fragments), name_fragments
    name = '.'.join(name_fragments)
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


def query_cache(*name_fragments: t.Sequence[str]) -> t.Union[dict, TimingGroup, Timing]:
    """Request timing data from global cache."""
    return TimingCache.query(*name_fragments)


def normalize_overhead(samples: int = 10000, threshold: float = 1.0):
    """Investigate overhead of starting and stopping the timer.

    Do it so as to take the overhead into account when calculating actual execution times.
    """
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
