"""
Logging utility for TutorSchool Django Backend

Usage:
    from config.logger import get_logger
    
    logger = get_logger(__name__)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # With exception tracking
    try:
        # code
    except Exception as e:
        logger.exception("Something went wrong", exc_info=True)
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: The name of the module (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Pre-configured loggers for common use
django_logger = logging.getLogger('django')
auth_logger = logging.getLogger('auth_app')
tutor_logger = logging.getLogger('tutor')
learner_logger = logging.getLogger('learner')
subscription_logger = logging.getLogger('subscriptions')
sharing_logger = logging.getLogger('sharing')
