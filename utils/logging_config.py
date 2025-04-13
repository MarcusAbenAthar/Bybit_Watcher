# logging_config.py
# Configuração centralizada de logs com proteção contra duplicações e logs consistentes por dia.

import logging
import logging.config
from datetime import datetime
from pathlib import Path
import os

# Diretórios de log garantidos
log_root = Path("logs")
log_root.mkdir(exist_ok=True)
for sub in ["bot", "erros", "sinais"]:
    (log_root / sub).mkdir(parents=True, exist_ok=True)

# Nome fixo por data (evita múltiplos arquivos no mesmo dia)
log_data = datetime.now().strftime("%d-%m-%Y")
log_arquivo = log_root / "bot" / f"bot_{log_data}.log"
log_erros = log_root / "erros" / f"erros_{log_data}.log"
log_sinais = log_root / "sinais" / f"sinais_{log_data}.log"

# Nível personalizado EXECUÇÃO
EXECUTION_LEVEL = 15
logging.addLevelName(EXECUTION_LEVEL, "EXECUÇÃO")


def execution(self, message, *args, **kwargs):
    if self.isEnabledFor(EXECUTION_LEVEL):
        self._log(EXECUTION_LEVEL, message, args, **kwargs)


logging.Logger.execution = execution

# Configuração base (dinâmica via configurar_logging)
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
            "filename": str(log_arquivo),
            "formatter": "detalhado",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_sinais),
            "formatter": "sinais",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "level": "INFO",
            "encoding": "utf-8",
        },
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_erros),
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
            "level": "INFO",  # Este nível pode ser alterado para DEBUG mais tarde
            "propagate": False,
        },
        "plugins": {"level": "INFO", "propagate": True},
        "sinais": {"handlers": ["sinais"], "level": "INFO", "propagate": False},
        "ccxt": {"handlers": ["null"], "propagate": False},
        "urllib3": {"handlers": ["null"], "propagate": False},
    },
}


def configurar_logging(debug_enabled=False):
    """
    Configura o sistema de logging com base na flag debug_enabled.
    """
    try:
        # Se debug_enabled for True, ajusta o nível para DEBUG
        level = logging.DEBUG if debug_enabled else logging.INFO

        BASE_CONFIG["loggers"][""]["level"] = level
        BASE_CONFIG["loggers"]["plugins"]["level"] = level

        logging.config.dictConfig(BASE_CONFIG)

        logger = logging.getLogger(__name__)
        logger.info("Sistema de logging inicializado")
        return logger
    except Exception as e:
        print(f"[LOGGING ERROR] Falha ao configurar logging: {e}")
        raise


def get_logger(nome: str, debug_enabled=False) -> logging.Logger:
    """
    Obtém um logger seguro contra duplicações e pronto para uso, com configuração de nível dinâmico.
    """
    # Configura o logging quando o logger for criado
    logger = logging.getLogger(nome)
    if not logger.hasHandlers():
        configurar_logging(
            debug_enabled
        )  # Configura o logging conforme a flag debug_enabled
    return logger
