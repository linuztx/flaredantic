import logging

# ANSI colors for console output
GREEN = "\033[92m"
RESET = "\033[0m"

def setup_logger(verbose: bool = False) -> logging.Logger:
    """Configure and return a logger with custom formatting"""
    logger = logging.getLogger("flaredantic")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler with custom formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger 