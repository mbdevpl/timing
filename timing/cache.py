"""Cache of timing results."""

import collections
import datetime
import typing as t

from .timing import Timing
from .group import TimingGroup


class TimingCache:
    """Global cache for timing results."""

    hierarchical: t.Dict[str, dict] = collections.OrderedDict()
    """Hierarchy of TimingGroup objects structured in a tree that branches
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

    flat: t.Dict[str, TimingGroup] = collections.OrderedDict()
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

    chronological: t.List[t.Tuple[datetime.datetime, Timing]] = []
    """Individual Timing objects in the order that they were started in."""

    @classmethod
    def clear(cls) -> None:
        cls.hierarchical = collections.OrderedDict()
        cls.flat = collections.OrderedDict()
        cls.chronological = []

    @classmethod
    def query(cls, *name_fragments: str) -> t.Union[dict, TimingGroup, Timing]:
        """Query the cache using one or more name fragments."""
        assert name_fragments
        assert all(isinstance(_, str) and _ for _ in name_fragments), name_fragments
        normalized_name_fragments = '.'.join(name_fragments).split('.')
        timing_cache = TimingCache.hierarchical
        for _, name_fragment in enumerate(normalized_name_fragments):
            timing_cache = timing_cache[name_fragment]
        return timing_cache['.']
