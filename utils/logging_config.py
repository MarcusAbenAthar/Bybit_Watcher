"""
Configuração centralizada de logs.

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

import logging.config
import logging.handlers
from datetime import datetime
from pathlib import Path

# Criar diretório de logs se não existir
Path("logs").mkdir(exist_ok=True)

# Configurações Base
BASE_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detalhado": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simples": {
            "format": "%(asctime)s | %(levelname)-8s | %(filename)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "sinais": {
            "format": "%Y-%m-%d %H:%M:%S | SINAL | %(filename)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
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
            "filename": f"logs/bot_{datetime.now():%Y-%m-%d}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "DEBUG",
        },
        # Handler para sinais de trading
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/sinais_{datetime.now():%Y-%m-%d}.log",
            "formatter": "sinais",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "INFO",
        },
        # Handler para erros
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/erros_{datetime.now():%Y-%m-%d}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "ERROR",
        },
        # Handler para info
        "info": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/info_{datetime.now():%Y-%m-%d}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "INFO",
        },
        # Handler para warning
        "warning": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/warning_{datetime.now():%Y-%m-%d}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "WARNING",
        },
        # Handler para critical
        "critical": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/critical_{datetime.now():%Y-%m-%d}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "CRITICAL",
        },
    },
    "loggers": {
        # Logger raiz
        "": {
            "handlers": ["console", "arquivo", "erros", "critical"],
            "level": "DEBUG",
            "propagate": True,
        },
        # Logger específico para sinais
        "sinais": {
            "handlers": ["sinais"],
            "level": "INFO",
            "propagate": False,
        },
        # Logger específico para critical
        "critical": {
            "handlers": ["critical"],
            "level": "CRITICAL",
            "propagate": False,
        },
        # Loggers específicos para cada nível
        "info": {
            "handlers": ["info"],
            "level": "INFO",
            "propagate": False,
        },
        "warning": {
            "handlers": ["warning"],
            "level": "WARNING",
            "propagate": False,
        },
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
