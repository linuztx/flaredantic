import logging

# ANSI colors for console output
GREEN = "\033[92m"
RESET = "\033[0m"

# Global logger instance
_logger = None

def setup_logger(verbose: bool = False) -> logging.Logger:
    """Configure and return a logger with custom formatting"""
    global _logger
    
    # Return existing logger if already configured
    if _logger is not None:
        _logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        return _logger
    
    _logger = logging.getLogger("flaredantic")
    _logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    _logger.handlers.clear()
    
    # Create console handler with custom formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # Log GitHub URL and version
    _logger.info("https://github.com/linuztx/flaredantic")
    
    return _logger 