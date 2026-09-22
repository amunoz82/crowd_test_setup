"""Module for setting up the logging system."""

import logging
import sys

def setup_logging(logger_name: str = None) -> logging.Logger:
    """Configures the application's logging system."""
    
    # Get the root logger
    logger = logging.getLogger(logger_name) 
    logger.setLevel(logging.DEBUG) # Set the lowest level to capture

    # Handler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Only show INFO/WARNING/ERROR to console
    
    # Handler for file output
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Apply and Add Handlers
    console_handler.setFormatter(formatter)
    # file_handler.setFormatter(formatter)
    
    if not logger.handlers: # Prevent setting up handlers multiple times
        logger.addHandler(console_handler)
        # logger.addHandler(file_handler)

    return logger