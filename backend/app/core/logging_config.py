import logging
import re

# Regex patterns matching Riot API keys and potential authorization tokens
RIOT_API_KEY_REGEX = re.compile(r"RGAPI-[a-zA-Z0-9\-]{20,}", re.IGNORECASE)
GENERIC_BEARER_REGEX = re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE)
RIOT_TOKEN_HEADER_REGEX = re.compile(
    r"(X-Riot-Token[\'\"]?:\s*[\'\"]?)[^\'\"\s]+", re.IGNORECASE
)


def sanitize_sensitive_data(text: str) -> str:
    """Sanitize any API keys, tokens, or credential headers from a string."""
    if not isinstance(text, str):
        text = str(text)

    sanitized = RIOT_API_KEY_REGEX.sub("RGAPI-[REDACTED]", text)
    sanitized = GENERIC_BEARER_REGEX.sub(r"\1[REDACTED]", sanitized)
    sanitized = RIOT_TOKEN_HEADER_REGEX.sub(r"\1[REDACTED]", sanitized)
    return sanitized


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts API keys and sensitive tokens from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: sanitize_sensitive_data(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    sanitize_sensitive_data(a) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


def setup_secure_logging(log_level: int = logging.INFO) -> None:
    """Configure loggers with the sensitive data redaction filter."""

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    filter_instance = SensitiveDataFilter()
    for handler in root_logger.handlers:
        handler.addFilter(filter_instance)

    app_logger = logging.getLogger("rifttracker")
    app_logger.setLevel(log_level)
    app_logger.addFilter(filter_instance)
