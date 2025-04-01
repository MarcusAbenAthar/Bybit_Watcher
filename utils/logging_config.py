# logging_config.py
# Configuração centralizada de logs

"""
Configuração centralizada de logs. Arquivo logging_config.py

Regras de Ouro:
1. Autonomo - Rotação automática de logs
2. Criterioso - Níveis apropriados
3. Seguro - Tratamento de erros
4. Certeiro - Logs precisos
5. Eficiente - Performance otimizada
6. Clareza - Formato padronizado
7. Modular - Configuração única
8. Plugins - Logs específicos por plugin
9. Testável - Fácil mock
10. Documentado - Bem documentado
"""

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
        "simples": {
            "format": "%(asctime)s | %(levelname)-8s | %(filename)s | %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
        "sinais": {
            "format": "%d-%m-%Y %H:%M:%S | SINAL | %(filename)s | %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detalhado",
            "level": EXECUTION_LEVEL,  # Garante que EXECUÇÃO seja visível
        },
        "arquivo": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/bot/bot_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": EXECUTION_LEVEL,  # Garante que EXECUÇÃO seja visível
            "encoding": "utf-8",
        },
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/sinais/sinais_{datetime.now():%d-%m-%Y}.log",
            "formatter": "sinais",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "INFO",
            "encoding": "utf-8",
        },
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/erros/erros_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "ERROR",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "arquivo", "erros"],
            "level": EXECUTION_LEVEL,  # Nível mínimo para raiz
            "propagate": True,
        },
        "sinais": {"handlers": ["sinais"], "level": "INFO", "propagate": False},
        "plugins": {
            "level": EXECUTION_LEVEL,  # Garante EXECUÇÃO para plugins
            "handlers": ["console", "arquivo", "erros"],
            "propagate": False,
        },
        "plugins.gerente_plugin": {
            "level": EXECUTION_LEVEL,
            "handlers": ["console", "arquivo"],
            "propagate": False,
        },
    },
}


def configurar_logging(config=None):
    """Configura o sistema de logging com base no config fornecido.

    Args:
        config (dict, optional): Configurações do sistema, incluindo "logging.debug_enabled".
    """
    try:
        debug_enabled = (
            config.get("logging", {}).get("debug_enabled", False) if config else False
        )
        level = (
            logging.DEBUG if debug_enabled else EXECUTION_LEVEL
        )  # Usa EXECUTION como mínimo

        # Ajusta os níveis dos loggers
        BASE_CONFIG["loggers"][""]["level"] = level
        BASE_CONFIG["loggers"]["plugins"]["level"] = level
        BASE_CONFIG["loggers"]["plugins.gerente_plugin"]["level"] = level

        logging.config.dictConfig(BASE_CONFIG)
        logger = logging.getLogger(__name__)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("ccxt").setLevel(logging.CRITICAL)
        logging.getLogger("requests").setLevel(logging.CRITICAL)
        logger.info("Sistema de logging inicializado")
        return logger
    except Exception as e:
        print(f"Erro ao configurar logging: {e}")
        raise


def get_logger(nome: str) -> logging.Logger:
    """
    Obtém um logger configurado.

    Args:
        nome: Nome do logger

    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(nome)
