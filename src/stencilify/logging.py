"""Logging configuration for stencilify."""

import logging
import sys


def setup_logging(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        verbose: Enable verbose (DEBUG) logging
        quiet: Suppress all but ERROR messages

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("stencilify")

    # Set level based on flags
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to 'stencilify')

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "stencilify")
