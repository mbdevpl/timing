.. role:: python(code)
    :language: python


======
timing
======

.. image:: https://img.shields.io/pypi/v/timing.svg
    :target: https://pypi.org/project/timing
    :alt: package version from PyPI

.. image:: https://travis-ci.com/mbdevpl/timing.svg?branch=master
    :target: https://travis-ci.com/mbdevpl/timing
    :alt: build status from Travis CI

.. image:: https://codecov.io/gh/mbdevpl/timing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/mbdevpl/timing
    :alt: test coverage from Codecov

.. image:: https://img.shields.io/github/license/mbdevpl/timing.svg
    :target: https://github.com/mbdevpl/timing/blob/master/NOTICE
    :alt: license

Timing module was created to simplify logging of timings of selected parts of an application.

.. contents::
    :backlinks: none


How to use
==========

Recommended initialization is as follows.

.. code:: python

    import timing

    _TIME = timing.get_timing_group(__name__)  # type: timing.TimingGroup


This follows the conventions of :python:`logging` module.

.. code:: python

    import logging

    _LOG = logging.getLogger(__name__)

Any name can be used instead of :python:`__name__`.
However, if a names of format :python:`module.sub.subsub` are used, this will create a timing
hierarchy where each timing data is stored in its proper location and can be queried easier.

The resulting :python:`_TIME` object is used to create individual timers,
and will handle storing results in cache, which later can be used to obtain timing statistics.

You can obtain the timer object directly via :python:`start(name)` method.
You'll need to manually call :python:`stop()` in this case.

.. code:: python

   timer = _TIME.start('spam')  # type: timing.Timing
   spam()
   more_spam()
   timer.stop()


You can also obtain the timer object indirectly via :python:`measure(name)` context manager.
The context manager will take care of calling :python:`stop()` at the end.

.. code:: python

    with _TIME.measure('ham') as timer:  # type: timing.Timing
        ham()
        more_ham()


And if you want to time many repetitions of the same action (e.g. for statistical significance)
you can use :python:`measure_many(name[, samples][, threshold])` generator.

You can decide how many times you want to measure via :python:`samples` parameter
and how many seconds at most you want to spend on measurements via :python:`threshold` parameter

.. code:: python

    for timer in _TIME.measure_many('eggs', samples=1000):  # type: timing.Timing
        eggs()
        more_eggs()

    for timer in _TIME.measure_many('bacon', threshold=0.5):  # type: timing.Timing
        bacon()
        more_bacon()

    for timer in _TIME.measure_many('tomatoes', samples=500, threshold=0.5):  # type: timing.Timing
        tomatoes()
        more_tomatoes()


Also, you can use :python:`measure` and :python:`measure(name)` as decorator.
In this scenario you cannot access the timings directly, but the results will be stored
in the timing group object, as well as in the global cache unless you configure the timing
to not use the cache.

.. code:: python

    import timing

    _TIME = timing.get_timing_group(__name__)

    @_TIME.measure
    def recipe():
        ham()
        eggs()
        bacon()

    @_TIME.measure('the_best_recipe')
    def bad_recipe():
        spam()
        spam()
        spam()


Then, after calling each function the results can be accessed through :python:`summary` property.

.. code:: python

    recipe()
    bad_recipe()
    bad_recipe()

    assert _TIME.summary['recipe']['samples'] == 1
    assert _TIME.summary['the_best_recipe']['samples'] == 2


The :python:`summary` property is dynamically computed on first access. Subsequent accesses
will not recompute the values, so if you need to access the updated results,
call the :python:`summarize()` method.

.. code:: python

    recipe()
    assert _TIME.summary['recipe']['samples'] == 1

    bad_recipe()
    bad_recipe()
    assert _TIME.summary['the_best_recipe']['samples'] == 2  # will fail
    _TIME.summarize()
    assert _TIME.summary['the_best_recipe']['samples'] == 2  # ok


Further API and documentation are in development.


See these examples in action in `<examples.ipynb>`_ notebook.


Requirements
============

Python version 3.5 or later.

Python libraries as specified in `<requirements.txt>`_.

Building and running tests additionally requires packages listed in `<test_requirements.txt>`_.

Tested on Linux and OS X.
