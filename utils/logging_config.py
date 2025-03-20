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
        # Handler para console
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detalhado",
            "level": "DEBUG",
        },
        # Handler para log geral
        "arquivo": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/bot/bot_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "DEBUG",
            "encoding": "utf-8",  # Adicionado
        },
        # Handler para sinais de trading
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/sinais/sinais_{datetime.now():%d-%m-%Y}.log",
            "formatter": "sinais",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "INFO",
            "encoding": "utf-8",  # Adicionado
        },
        # Handler para erros
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/erros/erros_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "ERROR",
            "encoding": "utf-8",  # Adicionado
        },
    },
    "loggers": {
        # Logger raiz
        "": {
            "handlers": ["console", "arquivo", "erros"],
            "level": "DEBUG",
            "propagate": True,
        },
        # Logger específico para sinais
        "sinais": {"handlers": ["sinais"], "level": "INFO", "propagate": False},
        # Loggers específicos para cada plugin
        "plugins": {
            "level": "DEBUG",
            "handlers": ["console", "arquivo", "erros"],
            "propagate": False,
        },
        # Logger específico para gerente_plugin
        "plugins.gerente_plugin": {
            "level": "DEBUG",
            "handlers": ["console", "arquivo"],
            "propagate": False,
        },
    },
}


def configurar_logging():
    """Configura o sistema de logging."""
    try:
        logging.config.dictConfig(BASE_CONFIG)
        logger = logging.getLogger(__name__)
        # Bloqueia completamente logs de bibliotecas externas
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("ccxt").setLevel(logging.CRITICAL)
        logging.getLogger("requests").setLevel(logging.CRITICAL)
        logger.info("Sistema de logging inicializado")
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
