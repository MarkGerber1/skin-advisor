import json
import logging
import logging.handlers
import os
from datetime import datetime


class JSONLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, "payload"):
            payload["payload"] = getattr(record, "payload")
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_catalog_logger() -> logging.Logger:
    logger = logging.getLogger("catalog")
    if logger.handlers:
        return logger
    os.makedirs("logs", exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        filename="logs/catalog_errors.jsonl",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(JSONLineFormatter())
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger








