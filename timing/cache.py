
import collections
import typing as t


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
    def clear(cls) -> None:
        cls.hierarchical = collections.OrderedDict()
        cls.flat = collections.OrderedDict()
        cls.chronological = []

    @classmethod
    def query(cls, name: str) -> t.Union[dict, 'TimingGroup', 'Timing']:
        assert isinstance(name, str), type(name)
        name_fragments = name.split('.')
        timing_cache = TimingCache.hierarchical
        for _, name_fragment in enumerate(name_fragments):
            timing_cache = timing_cache[name_fragment]
        return timing_cache['.']
