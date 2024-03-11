"""Handling of group of timings."""

import contextlib
import datetime
import functools
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

        self._name: str = name
        self._timings: t.List[Timing] = []
        self._summary: t.Optional[t.Dict[str, t.Any]] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def timings(self) -> t.List[Timing]:
        return list(self._timings)

    @property
    def summary(self) -> t.Dict[str, t.Any]:
        """Return a collection of statistics for the timings in this group.

        Calculate statistics if not already calculated, and use cached values otherwise.
        """
        if self._summary is None:
            self.summarize()
        assert self._summary is not None
        return self._summary

    def start(self, name: str) -> Timing:
        """Create a Timing belonging to this TimingGroup and start it."""
        if '.' in name:
            from .utils import get_timing_group  # pylint: disable = import-outside-toplevel
            prefix, _, suffix = name.rpartition('.')
            group = get_timing_group(self._name, prefix)
            return group.start(suffix)

        timing = Timing(name)
        if TimingConfig.enable_cache:
            from .cache import TimingCache  # pylint: disable = import-outside-toplevel
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

    def measure(self, function_or_name: t.Callable | str | None = None, name: str | None = None):
        """Use this method as a context manager or decorator.

        As context manager:

        with ....measure(name) as timer:
            ...

        As decorator:

        @measure
        def ...

        @measure(name)
        def ...
        """
        if function_or_name is not None:
            if isinstance(function_or_name, str):
                assert name is None, 'name given in the first argument, 2nd argument must be None'
                function, name = None, function_or_name
            else:
                function = function_or_name
        else:
            assert name is not None, 'at least one argument to measure() is required'
            function = None
        if function is None:
            # in practice this path is also taken when @measure(name) is used,
            # but since contextlib uses ContextDecorator, it works
            assert name is not None
            return self._measure_context(name)
        assert isinstance(function, types.FunctionType)
        return self._measure_decorator(function, name)

    @contextlib.contextmanager
    def _measure_context(self, name: str) -> t.Generator[Timing, None, None]:
        """Return the just-started timer as context variable."""
        timer = self.start(name)
        yield timer
        timer.stop()

    def _measure_decorator(self, function: types.FunctionType, name: str | None = None):
        """Return the original function wrapped in a timing context."""
        if name is None:
            name = function.__name__

        @functools.wraps(function)
        def function_wrapper(*args, **kwargs):
            with self._measure_context(name):
                return function(*args, **kwargs)
        return function_wrapper

    def measure_many(self, name: str, samples: t.Optional[int] = None,
                     threshold: t.Optional[float] = None) -> t.Iterator[Timing]:
        """Iterate and time each iteration until some iterations or until some time passes.

        Use via 'for timer in measure_many('name'[, samples][, threshold]).
        """
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
                assert timer.elapsed is not None
                threshold -= timer.elapsed
                if threshold <= 0:
                    break

    def query_cache(self, *name_fragments: str) -> t.Union[dict, 'TimingGroup', Timing]:
        """Query the cache within the scope of this timing group."""
        from .cache import TimingCache  # pylint: disable = import-outside-toplevel
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
        return f'{type(self).__name__}({", ".join([str(_) for _ in args])})'

    def __repr__(self):
        return str(self)
