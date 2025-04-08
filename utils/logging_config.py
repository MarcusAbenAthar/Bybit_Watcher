# logging_config.py
# Configuração centralizada de logs sem duplicações

import logging
import logging.config
import logging.handlers
from datetime import datetime
import os
from pathlib import Path

# Criação de diretórios de log
Path("logs").mkdir(exist_ok=True)
os.makedirs("logs/erros", exist_ok=True)
os.makedirs("logs/bot", exist_ok=True)
os.makedirs("logs/sinais", exist_ok=True)

# Nível personalizado entre DEBUG e INFO
EXECUTION_LEVEL = 15
logging.addLevelName(EXECUTION_LEVEL, "EXECUÇÃO")


def execution(self, message, *args, **kwargs):
    if self.isEnabledFor(EXECUTION_LEVEL):
        self._log(EXECUTION_LEVEL, message, args, **kwargs)


logging.Logger.execution = execution

# Configuração base
BASE_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detalhado": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
        "sinais": {
            "format": "%(asctime)s | SINAL | %(filename)s | %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detalhado",
            "level": "DEBUG",
        },
        "arquivo": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/bot/bot_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/sinais/sinais_{datetime.now():%d-%m-%Y}.log",
            "formatter": "sinais",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "level": "INFO",
            "encoding": "utf-8",
        },
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/erros/erros_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "level": "ERROR",
            "encoding": "utf-8",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "arquivo", "erros"],
            "level": "INFO",  # Vai ser ajustado dinamicamente
            "propagate": False,
        },
        # Loggers filhos só propagam
        "plugins": {"level": "INFO", "propagate": True},
        "sinais": {"handlers": ["sinais"], "level": "INFO", "propagate": False},
        "ccxt": {"handlers": ["null"], "propagate": False},
        "urllib3": {"handlers": ["null"], "propagate": False},
    },
}


def configurar_logging(config=None):
    """Configura o sistema de logging com base nas opções do config."""
    try:
        debug_enabled = False
        if config and config.get("logging", {}).get("debug_enabled"):
            debug_enabled = True

        level = logging.DEBUG if debug_enabled else EXECUTION_LEVEL
        BASE_CONFIG["loggers"][""]["level"] = level
        BASE_CONFIG["loggers"]["plugins"]["level"] = level

        logging.config.dictConfig(BASE_CONFIG)

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Logging configurado com debug_enabled={debug_enabled}, nível={logging.getLevelName(level)}"
        )
        logger.info("Sistema de logging inicializado")
        return logger
    except Exception as e:
        print(f"Erro ao configurar logging: {e}")
        raise


def get_logger(nome: str) -> logging.Logger:
    """Obtém um logger configurado e seguro contra duplicações."""
    logger = logging.getLogger(nome)
    return logger
