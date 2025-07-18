import logging

def setup_logging():
    """
    Configura un sistema di logging standardizzato per tutti i bot.
    Le informazioni verranno stampate sulla console con un formato chiaro.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )