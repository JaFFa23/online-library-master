import sys
from loguru import logger
from app.core.config import settings

def setup_logging() -> None:
    """
    Минимальная настройка loguru.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
