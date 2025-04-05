# logging_config.py
# Configuração centralizada de logs

import logging
import logging.config
import logging.handlers
from datetime import datetime
import os
from pathlib import Path

# Criar diretório de logs e suas subpastas se não existir
Path("logs").mkdir(exist_ok=True)
os.makedirs("logs/erros", exist_ok=True)
os.makedirs("logs/bot", exist_ok=True)
os.makedirs("logs/sinais", exist_ok=True)

# Definir nível personalizado EXECUÇÃO (entre DEBUG=10 e INFO=20)
EXECUTION_LEVEL = 15
logging.addLevelName(EXECUTION_LEVEL, "EXECUÇÃO")


def execution(self, message, *args, **kwargs):
    if self.isEnabledFor(EXECUTION_LEVEL):
        self._log(EXECUTION_LEVEL, message, args, **kwargs)


logging.Logger.execution = execution

# Configurações Base
BASE_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detalhado": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
        "sinais": {
            "format": "%d-%m-%Y %H:%M:%S | SINAL | %(filename)s | %(message)s",
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
            "maxBytes": 10485760,
            "backupCount": 10,
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/sinais/sinais_{datetime.now():%d-%m-%Y}.log",
            "formatter": "sinais",
            "maxBytes": 10485760,
            "backupCount": 10,
            "level": "INFO",
            "encoding": "utf-8",
        },
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/erros/erros_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,
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
            "level": "INFO",  # Nível padrão, ajustado dinamicamente
            "propagate": True,
        },
        # "sinais": {"handlers": ["sinais"], "level": "INFO", "propagate": False},
        "plugins": {"handlers": ["console", "arquivo", "erros"], "level": "INFO"},
        "ccxt": {"handlers": ["null"], "propagate": False},
        "urllib3": {"handlers": ["null"], "propagate": False},
    },
}


def configurar_logging(config=None):
    """Configura o sistema de logging com base no config fornecido."""
    try:
        # Extrai debug_enabled do config
        debug_enabled = False
        if config and "logging" in config and "debug_enabled" in config["logging"]:
            debug_enabled = config["logging"]["debug_enabled"]

        # Define o nível com base em debug_enabled
        level = logging.DEBUG if debug_enabled else EXECUTION_LEVEL
        BASE_CONFIG["loggers"][""]["level"] = level
        BASE_CONFIG["loggers"]["plugins"]["level"] = level

        # Aplica a configuração
        logging.config.dictConfig(BASE_CONFIG)

        # Logger para validação
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
    """Obtém um logger configurado."""
    return logging.getLogger(nome)
