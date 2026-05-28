import logging
import sys
from backend.app.config import settings

def setup_logger():
    """
    Sets up application-wide logger configurations.
    Returns a configured logging instance.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Map the level string from config to logging constants
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    log_level = level_map.get(settings.log_level.lower(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("ai_interview_assistant")
    logger.setLevel(log_level)
    return logger

# Single logger instance for easy import
logger = setup_logger()
