import logging
from logging.handlers import RotatingFileHandler
from config.server_config import ServerConfig

def setup_audit_logger():
    """Configure audit logger with rotating file handler."""
    cfg = ServerConfig.LOGGING_CONFIG
    logger = logging.getLogger("audit")
    logger.setLevel(cfg["loggers"]["qshield"]["level"])

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(cfg["handlers"]["console"]["level"])
    ch.setFormatter(logging.Formatter(cfg["formatters"]["standard"]["format"]))
    logger.addHandler(ch)

    # File handler
    fh_cfg = cfg["handlers"]["file"]
    fh = RotatingFileHandler(
        filename=fh_cfg["filename"],
        maxBytes=fh_cfg["maxBytes"],
        backupCount=fh_cfg["backupCount"]
    )
    fh.setLevel(fh_cfg["level"])
    fh.setFormatter(logging.Formatter(cfg["formatters"]["detailed"]["format"]))
    logger.addHandler(fh)

    return logger
