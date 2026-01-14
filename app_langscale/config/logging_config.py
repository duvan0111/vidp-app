# app_langscale/config/logging_config.py
import logging

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

def setup_logging():
    """Configure logging (console only, no file)"""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler()  # Console only
        ]
    )
    return logging.getLogger("LanguageDetectionAPI")
