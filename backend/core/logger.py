import sys
from loguru import logger
from backend.core.config import settings

logger.remove()

fmt = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.add(sys.stderr, format=fmt, level="DEBUG" if settings.debug else "INFO")
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    format=fmt,
    level="INFO",
)

__all__ = ["logger"]
