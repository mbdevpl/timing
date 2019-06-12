"""Logging-like interface for timing the application.

First version written on 7 September 2016.

Copyright 2016, 2018  Mateusz Bysiek https://mbdevpl.github.io/
"""

# pylint: disable=too-few-public-methods

import collections
import contextlib
import datetime
import logging
import statistics
import time
import types
import typing as t

import numpy as np

if __debug__:
    _LOG = logging.getLogger(__name__)


class TimingConfig:

    """Global configuration of timing."""

    enable_cache = True
    overhead = 0.0


class TimingCache:

    """Global cache for timing results."""

    hierarchical = collections.OrderedDict()
    """Hierarchy of TimingGroup objects strucutred in a tree that branches
    at '.' in the TimingGroup names.

    For example, having timing groups named after some example modules:

    - TimingGroup('spam.eggs.spam')
    - TimingGroup('spam.spam')
    - TimingGroup('eggs.ham')
    - TimingGroup('spam.eggs')

    the hierarchy would be:

    hierarchical_timing_cache = {
        'spam': {
            'eggs': {
                '.': TimingGroup('spam.eggs'),
                'spam': {
                    '.': TimingGroup('spam.eggs.spam')
                    }
                },
            'spam': {
                '.': TimingGroup('spam.spam')
                }
            },
        'eggs': {
            'ham': {
                '.': TimingGroup('eggs.ham')
                }
            }
        }
    """

    flat = collections.OrderedDict()
    """Flattened view of the TimingGroup objects hierarchy.

    For example, having timing groups named after some example modules:

    - TimingGroup('spam.eggs.spam')
    - TimingGroup('spam.spam')
    - TimingGroup('eggs.ham')
    - TimingGroup('spam.eggs')

    the flattened view would simply be:

    flat_timing_cache = {
        'spam.eggs.spam': TimingGroup('spam.eggs.spam')
        'spam.spam': TimingGroup('spam.spam')
        'eggs.ham': TimingGroup('eggs.ham')
        'spam.eggs': TimingGroup('spam.eggs')
        }
    """

    chronological = []
    """Individual Timing objects in the order that they were started in."""

    @classmethod
    def clear(cls):
        cls.hierarchical = collections.OrderedDict()
        cls.flat = collections.OrderedDict()
        cls.chronological = []


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


class TimingGroup(dict):

    """Group of timings."""

    def __init__(self, name: str):
        super().__init__()
        assert isinstance(name, str)

        self._name = name  # type: str
        self._timings = []  # type: t.List[Timing]
        self._summary = None

    @property
    def name(self):
        return self._name

    @property
    def timings(self):
        return [_ for _ in self._timings]

    @property
    def summary(self):
        if self._summary is None:
            self.summarize()
        return self._summary

    def start(self, name: str) -> Timing:
        """Create a Timing belonging to this TimingGroup and start it."""
        if '.' in name:
            prefix, _, suffix = name.rpartition('.')
            group = get_timing_group('{}.{}'.format(self._name, prefix))
            # import ipdb; ipdb.set_trace()
            return group.start(suffix)

        timing = Timing(name)
        if TimingConfig.enable_cache:
            self._timings.append(timing)
            if self._name in TimingCache.flat and TimingCache.flat[self._name] is self:
                cache_entry = (datetime.datetime.now(), timing)
                TimingCache.chronological.append(cache_entry)
        if name in self:
            self[name].append(timing)
        else:
            self[name] = [timing]
        timing.start()
        return timing

    def measure(self, function: types.FunctionType = None, name: str = None):
        if name is None and function is not None and isinstance(function, str):
            name = function
            function = None
        if function is None:
            return self._measure_context(name)
        assert isinstance(function, types.FunctionType)
        return self._measure_decorator(function, name)

    @contextlib.contextmanager
    def _measure_context(self, name: str):
        timer = self.start(name)
        yield timer
        timer.stop()

    def _measure_decorator(self, function: types.FunctionType,
                           name: str = None) -> types.FunctionType:
        if name is None:
            name = function.__name__

        def function_wrapper(*args, **kwargs):
            with self.measure(name):
                return function(*args, **kwargs)
        return function_wrapper

    def measure_many(self, name: str, samples: t.Optional[int] = None,
                     threshold: t.Optional[float] = None):
        """Use via 'for timer in measure_many('name'[, samples][, threshold])."""
        assert samples is not None or threshold is not None, (samples, threshold)
        assert samples is None or isinstance(samples, int) and samples > 0, samples
        assert threshold is None or threshold > 0, threshold
        while True:
            timer = self.start(name)
            yield timer
            timer.stop()
            if samples is not None:
                samples -= 1
                if samples == 0:
                    break
            if threshold is not None:
                threshold -= timer.elapsed
                if threshold <= 0:
                    break

    def summarize(self) -> None:
        """Calculate various statistics from the raw data."""
        self._summary = {}
        for name, timings in self.items():
            elapsed = [_.elapsed for _ in timings]
            # np.ndarray((len(timings),), dtype=float)
            array = np.array(elapsed, dtype=float)
            self._summary[name] = {
                'data': array.tolist(),
                'samples': len(array),
                'min': array.min(),
                'max': array.max(),
                'mean': array.mean(),
                'median': np.median(array),
                'var': array.var(),
                'stddev': array.std()}

    def __eq__(self, other):
        if not isinstance(other, TimingGroup):
            return False
        return self._name == other.name and self._timings == other.timings

    def __str__(self):
        args = [self._name] + self._timings
        return '{}({})'.format(type(self).__name__, ', '.join([str(_) for _ in args]))

    def __repr__(self):
        return str(self)


def get_timing_group(name: t.Optional[str]) -> TimingGroup:
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
    assert isinstance(name, str), type(name)
    name_fragments = name.split('.')
    timing_cache = TimingCache.hierarchical
    for _, name_fragment in enumerate(name_fragments):
        timing_cache = timing_cache[name_fragment]
    return timing_cache['.']


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
