from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=level,
        colorize=True,
    )
    logger.add("logs/app.log", level=level, rotation="10 MB", retention=10)
