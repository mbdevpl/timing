
import time
import typing as t


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

    def _calculate_elapsed(self) -> None:
        assert isinstance(self._begin, float)
        assert isinstance(self._end, float)

        self._elapsed = self._end - self._begin

    @property
    def name(self) -> str:
        return self._name

    @property
    def begin(self) -> t.Optional[float]:
        return self._begin

    @property
    def end(self) -> t.Optional[float]:
        return self._end

    @property
    def elapsed(self) -> t.Optional[float]:
        return self._elapsed

    def start(self) -> None:
        """Start the timer."""
        self._begin = time.perf_counter()

    def stop(self) -> None:
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
