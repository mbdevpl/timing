
import logging

import colorlog

_HANDLER = logging.StreamHandler()
_HANDLER.setFormatter(colorlog.ColoredFormatter(
    '{name} [{log_color}{levelname}{reset}] {message}', style='{'))
logging.basicConfig(level=logging.INFO, handlers=[_HANDLER])
