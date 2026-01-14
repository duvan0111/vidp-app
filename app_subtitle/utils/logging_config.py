import logging
from config.settings import Settings

def setup_logging():
    """Configure logging for the application (console only, no file)."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Console only
        ]
    )
    
    # Set specific log levels
    logging.getLogger("whisper").setLevel(logging.WARNING)
    logging.getLogger("moviepy").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()