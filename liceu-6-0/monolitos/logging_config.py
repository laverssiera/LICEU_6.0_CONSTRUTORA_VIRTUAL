# logging_config.py
"""
Configuração de logging estruturado (JSON) e correlation ID para monolitos LICEU 6.0
"""
import logging
import sys
import uuid
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

# Utilitário para correlation ID
from contextvars import ContextVar
correlation_id_ctx = ContextVar("correlation_id", default=None)

def get_correlation_id():
    cid = correlation_id_ctx.get()
    if cid is None:
        cid = str(uuid.uuid4())
        correlation_id_ctx.set(cid)
    return cid

def set_correlation_id(cid: str):
    correlation_id_ctx.set(cid)
