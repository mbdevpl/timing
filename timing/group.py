
import contextlib
import datetime
import types
import typing as t

import numpy as np

from .config import TimingConfig
from .timing import Timing


class TimingGroup(dict):

    """Group of timings."""

    def __init__(self, name: str):
        super().__init__()
        assert isinstance(name, str)

        self._name = name  # type: str
        self._timings = []  # type: t.List[Timing]
        self._summary = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def timings(self) -> t.List[Timing]:
        return [_ for _ in self._timings]

    @property
    def summary(self) -> dict:
        if self._summary is None:
            self.summarize()
        return self._summary

    def start(self, name: str) -> Timing:
        """Create a Timing belonging to this TimingGroup and start it."""
        if '.' in name:
            from .utils import get_timing_group
            prefix, _, suffix = name.rpartition('.')
            group = get_timing_group(self._name, prefix)
            return group.start(suffix)

        timing = Timing(name)
        if TimingConfig.enable_cache:
            from .cache import TimingCache
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

    def query_cache(self, *name_fragments: t.Sequence[str]) -> t.Union[dict, 'TimingGroup', Timing]:
        """Query the cache within the scope of this timing group."""
        from .cache import TimingCache
        if not name_fragments:
            return TimingCache.query(self._name)
        return TimingCache.query(self._name, *name_fragments)

    def summarize(self) -> None:
        """Calculate (or recalculate) various statistics from the raw data."""
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
