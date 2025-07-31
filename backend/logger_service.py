import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logger(name: str = "RAGChatbot") -> logging.Logger:
    """
    Setup and return a configured logger instance
    
    Args:
        name: Logger name (default: "RAGChatbot")
    
    Returns:
        Configured logger instance
    """
    # Get log level from environment variable, default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Map string to logging level
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = log_level_map.get(log_level_str, logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

# Create and export the default logger instance
logger = setup_logger()

def get_logger():
    return logger