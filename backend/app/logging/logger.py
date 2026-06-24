import os
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        from app.logging.correlation import get_correlation_id
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id()
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def get_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        file_path = os.path.join(LOGS_DIR, filename)
        handler = RotatingFileHandler(file_path, maxBytes=10*1024*1024, backupCount=5)
        handler.setFormatter(JSONFormatter())
        
        # Also print to console
        console = logging.StreamHandler()
        console.setFormatter(JSONFormatter())
        
        logger.addHandler(handler)
        logger.addHandler(console)
        
    return logger

# Pre-configured loggers
audit_logger = get_logger("audit", "security.log")
error_logger = get_logger("error", "errors.log")
prediction_logger = get_logger("prediction", "prediction.log")
agent_logger = get_logger("agent", "agent.log")
system_logger = get_logger("system", "system.log")
