import logging
from config.settings import Settings

def setup_logging():
    """Configure logging for the application (console only)"""
    logging.basicConfig(
        level=getattr(logging, Settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Console only, no file logging
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()