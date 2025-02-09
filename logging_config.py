import logging
import logging.config
import datetime

# Obter a data de hoje no formato dia-mes-ano
data_hoje = datetime.datetime.now().strftime("%d-%m-%Y")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": f"logs/bot-{data_hoje}.log",  # Nome do arquivo com a data
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    "loggers": {"": {"handlers": ["console", "file"], "level": "INFO"}},
}


def setup_logging():
    """Configura o logging usando a configuração definida."""
    logging.config.dictConfig(LOGGING_CONFIG)
