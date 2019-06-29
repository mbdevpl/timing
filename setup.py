"""Setup script for timing package."""

import setup_boilerplate


class Package(setup_boilerplate.Package):

    """Package metadata."""

    name = 'timing'
    description = 'Simplify logging of timings of selected parts of an application.'
    url = 'https://github.com/mbdevpl/timing'
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only']
    keywords = ['timing', 'timer', 'time measurement', 'profiling', 'reproducibility']


if __name__ == '__main__':
    Package.setup()
