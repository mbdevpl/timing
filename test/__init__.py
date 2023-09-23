"""Initialization of tests for timing package."""

import boilerplates.logging


class TestsLogging(boilerplates.logging.Logging):
    """Test logging configuration."""

    packages = ['timing']


TestsLogging.configure()
