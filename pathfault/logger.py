import logging
import sys

# 레벨별 색깔 설정
COLOR_CODES = {
    'DEBUG': '\033[94m',     # 파랑
    'INFO': '\033[92m',      # 초록
    'WARNING': '\033[93m',   # 노랑
    'ERROR': '\033[91m',     # 빨강
    'CRITICAL': '\033[95m',  # 보라
}
RESET_CODE = '\033[0m'

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = COLOR_CODES.get(record.levelname, RESET_CODE)
        message = super().format(record)
        return f"{color}{message}{RESET_CODE}"

def setup_logger(name: str) -> logging.Logger:
    """
    Setup a colored logger for a specific module.
    """
    formatter = ColoredFormatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.NOTSET)

    if not logger.handlers:
        logger.addHandler(handler)
    return logger
