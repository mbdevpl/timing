"""Setup script for timing package."""

import boilerplates.setup


class Package(boilerplates.setup.Package):
    """Package metadata."""

    name = 'timing'
    description = 'Simplify logging of timings of selected parts of an application.'
    url = 'https://github.com/mbdevpl/timing'
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Benchmark',
        'Topic :: System :: Logging',
        'Typing :: Typed']
    keywords = ['timing', 'timer', 'time measurement', 'profiling', 'reproducibility']


if __name__ == '__main__':
    Package.setup()
