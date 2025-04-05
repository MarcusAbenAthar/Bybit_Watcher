# sinais_logging.py
from utils.logging_config import get_logger

logger = get_logger(__name__)
import datetime

# Obter a data de hoje no formato dia-mes-ano
data_hoje = datetime.datetime.now().strftime("%d-%m-%Y")

SINAIS_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "sinais": {"format": "%(asctime)s | %(levelname)-8s | SINAL: %(message)s"}
    },
    "handlers": {
        "sinais": {
            "class": "logging.FileHandler",
            "filename": f"logs/sinais/sinais_{data_hoje}.log",  # Nome do arquivo com a data
            "formatter": "sinais",
            "level": "INFO",
        }
    },
    "loggers": {
        "plugins.sinais_plugin": {
            "handlers": ["sinais"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

# fim do arquivo sinais_logging.py
