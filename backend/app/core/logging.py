"""Structured logging with redaction for tokens, keys, and private payloads."""

import logging
import re
import sys

SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE), r"\1[REDACTED]"),
    (
        re.compile(
            r"((?:api[_-]?key|secret|password|token)[\"']?\s*[:=]\s*[\"']?)[^\"'\s]+", re.IGNORECASE
        ),
        r"\1[REDACTED]",
    ),
]


def redact_sensitive_text(text: str) -> str:
    for pattern, repl in SENSITIVE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return redact_sensitive_text(msg)


def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = RedactingFormatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
