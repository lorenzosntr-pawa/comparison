"""Structured logging configuration for scraping workflows.

Uses structlog for structured, context-rich logging with support for
both development (console) and production (JSON) output formats.

Configuration:
    Set SCRAPE_LOG_JSON=true environment variable for JSON output
    (production). Default is colored console output (development).

Processors:
    - merge_contextvars: Inherits context from asyncio task
    - add_log_level: Adds level field to all log entries
    - TimeStamper: ISO format timestamps
    - StackInfoRenderer: Stack traces on exceptions

Usage:
    from src.scraping.logging import configure_logging, logger

    configure_logging()  # Call once at startup
    logger.info("scraping.started", platform="betpawa", events=42)
"""

import logging
import os

import structlog


def configure_logging(json_output: bool | None = None) -> None:
    """Configure structlog for scraping operations.

    Args:
        json_output: If True, output JSON format (production).
                     If False, output colored console format (development).
                     If None, reads from SCRAPE_LOG_JSON env var (default: False).
    """
    if json_output is None:
        json_output = os.environ.get("SCRAPE_LOG_JSON", "").lower() == "true"

    # Shared processors for both output modes
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Module-level logger for imports
logger = structlog.get_logger()
