"""Core module of the timing package."""

import enum
import time
import typing as t


@enum.unique
class TimingState(enum.IntEnum):
    """State of a timing."""

    NOT_STARTED = 0
    RUNNING = 1
    FINISHED = 2


class Timing:
    """Timing of performance-critical parts of application.

    Uses time.perf_counter(): https://docs.python.org/3/library/time.html#time.perf_counter
    """

    def __init__(self, name: str):
        assert isinstance(name, str), type(name)
        assert name
        # self._group = None  # type: t.Optional[TimingGroup]
        self._name: str = name
        self._state: int = 0
        self._begin: t.Optional[float] = None
        self._end: t.Optional[float] = None
        self._elapsed: t.Optional[float] = None

    def _calculate_elapsed(self) -> None:
        assert self._begin is not None, 'timing has not started yet'
        assert self._end is not None, 'timing has not finished yet'
        self._elapsed = self._end - self._begin

    @property
    def name(self) -> str:
        return self._name

    @property
    def begin(self) -> float:
        assert self._begin is not None, 'timing has not started yet'
        return self._begin

    @property
    def end(self) -> float:
        assert self._end is not None, 'timing has not finished yet'
        return self._end

    @property
    def elapsed(self) -> float:
        assert self._elapsed is not None, 'timing has not finished yet'
        return self._elapsed

    @property
    def state(self) -> TimingState:
        return {
            0: TimingState.NOT_STARTED,
            1: TimingState.RUNNING,
            2: TimingState.FINISHED,
        }[self._state]

    def start(self) -> None:
        """Start the timer."""
        self._state = 1
        self._end = None
        self._elapsed = None
        self._begin = time.perf_counter()

    def stop(self) -> None:
        """Stop the timer."""
        self._end = time.perf_counter()
        if self.state is not TimingState.RUNNING:
            self._end = None
        assert self.state is TimingState.RUNNING, 'timing has not started yet'
        self._state = 2
        self._calculate_elapsed()

    def __eq__(self, other):
        if not isinstance(other, Timing) or self.state is not other.state \
                or self._name != other.name:
            return False
        if self._state == 0:
            return True
        if self._begin != other.begin:
            return False
        if self.state == 1:
            return True
        return self._end == other.end

    def __str__(self):
        args = [self._name, self._begin, self._end, self._elapsed]
        return f'{type(self).__name__}({", ".join([str(_) for _ in args])})'

    def __repr__(self):
        return str(self)
