import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from tradeflow.core.config import Settings


def _shared_processors(settings: Settings) -> list[Processor]:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.api_log_format == "json":
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()))

    return processors


def configure_logging(settings: Settings) -> None:
    """Configure structlog and stdlib logging for the application."""
    log_level = getattr(logging, settings.api_log_level.upper(), logging.INFO)

    structlog.configure(
        processors=_shared_processors(settings),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(log_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def bind_request_context(**kwargs: Any) -> None:
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_request_context() -> None:
    structlog.contextvars.clear_contextvars()
