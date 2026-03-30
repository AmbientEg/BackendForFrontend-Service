import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("bff")
    if logger.handlers:
        return logger

    logger.setLevel(level.upper())
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _serialize_log(level: str, event: str, payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "payload": payload,
        },
        default=str,
    )


async def log_event_async(logger: logging.Logger, level: str, event: str, payload: dict[str, Any]) -> None:
    message = _serialize_log(level=level, event=event, payload=payload)
    await asyncio.to_thread(logger.log, getattr(logging, level.upper(), logging.INFO), message)
