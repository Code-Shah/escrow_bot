import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                'bot.log',
                maxBytes=1024 * 1024,  # 1MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Get logger
    logger = logging.getLogger(__name__)
    return logger

logger = setup_logger()
