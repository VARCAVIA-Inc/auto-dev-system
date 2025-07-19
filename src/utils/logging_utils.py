import logging

def setup_logging():
    """Configura un sistema di logging standardizzato per tutti i bot."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - (%(filename)s) - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )