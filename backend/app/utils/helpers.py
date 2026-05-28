import os
from backend.app.utils.logger import logger

def ensure_directory_exists(directory_path: str):
    """
    Checks if a directory exists, and creates it if it doesn't.
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.info(f"Created directory: {directory_path}")
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        raise
