"""Logging-like interface for timing the application.

First version written on 7 September 2016.

Copyright 2016, 2018  Mateusz Bysiek https://mbdevpl.github.io/
"""

import collections
import contextlib
import datetime
import logging
import statistics
import time
import typing as t

import numpy as np

if __debug__:
    _LOG = logging.getLogger(__name__)


class TimingConfig:

    enable_cache = True
    overhead = 0.0


class TimingCache:

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

    @contextlib.contextmanager
    def measure(self, name: str):
        timer = self.start(name)
        yield timer
        timer.stop()

    def measure_many(self, name: str, samples: int = None, treshold: float = 1.0):
        if samples is None:
            while True:
                raise NotImplementedError()
        for _ in range(0, samples):
            timer = self.start(name)
            yield timer
            timer.stop()
        return

    def summarize(self) -> None:
        self._summary = {}
        for name, timings in self.items():
            elapsed = [_.elapsed for _ in timings]
            # np.ndarray((len(timings),), dtype=float)
            array = np.array(elapsed, dtype=float)
            self._summary[name] = {
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
        return self._name == other.name and self._timings == other._timings

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
    assert isinstance(name, str), type(name)
    name_fragments = name.split('.')
    timing_cache = TimingCache.hierarchical
    for _, name_fragment in enumerate(name_fragments):
        timing_cache = timing_cache[name_fragment]
    return timing_cache['.']


def normalize_overhead(samples: int = 1000):
    """Investigate overhead of starting and stopping the timer.

    Do it so as to take the overhead into account when calculating actual execution times."""
    assert isinstance(samples, int)

    timing_overhead = Timing('timing overhead test')

    overheads = []
    for _ in range(samples):
        timing_overhead.start()
        timing_overhead.stop()
        overheads.append(timing_overhead.elapsed)

    mean = statistics.mean(overheads)
    median = statistics.median(overheads)
    stdev = statistics.pstdev(overheads, mean)
    variance = statistics.pvariance(overheads, mean)

    TimingConfig.overhead = median

    # assert stdev <= 0.000001
    # assert variance <= 0.000001

    if __debug__:
        _LOG.warning(
            'normalized overhead using %i samples: mean=%f, median=%f, stdev=%f, variance=%f',
            samples, mean, median, stdev, variance)


normalize_overhead()
