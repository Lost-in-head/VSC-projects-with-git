"""
Logging configuration for Cards-4-Sale.
Provides structured logging with file rotation and multiple handlers.
"""
import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path('logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

_configured = False


def configure_logging() -> None:
    """Configure application-wide logging (idempotent)."""
    global _configured
    if _configured:
        return

    LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel('INFO')

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / 'app.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / 'errors.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel('ERROR')

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel('WARNING')
    logging.getLogger('requests').setLevel('WARNING')
    logging.getLogger('werkzeug').setLevel('WARNING')

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
