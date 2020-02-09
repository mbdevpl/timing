"""Initialization of tests of timing package."""

import logging

import colorlog

_HANDLER = logging.StreamHandler()
_HANDLER.setFormatter(colorlog.ColoredFormatter(
    '{name} [{log_color}{levelname}{reset}] {message}', style='{'))
logging.basicConfig(level=logging.DEBUG, handlers=[_HANDLER])
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger('timing').setLevel(logging.DEBUG)
logging.getLogger('test').setLevel(logging.DEBUG)
