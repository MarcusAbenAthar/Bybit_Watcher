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
os.makedirs("logs/banco", exist_ok=True)

# Definir níveis personalizados
DATA_LEVEL = 25  # Entre INFO (20) e WARNING (30)
DATA_DEBUG_LEVEL = 15  # Entre DEBUG (10) e INFO (20)

# Adicionar níveis personalizados ao logging
logging.addLevelName(DATA_LEVEL, "DATA")
logging.addLevelName(DATA_DEBUG_LEVEL, "DATA-DEBUG")


# Funções helper pra usar os novos níveis
def data(self, message, *args, **kwargs):
    if self.isEnabledFor(DATA_LEVEL):
        self._log(DATA_LEVEL, message, args, **kwargs)


def data_debug(self, message, *args, **kwargs):
    if self.isEnabledFor(DATA_DEBUG_LEVEL):
        self._log(DATA_DEBUG_LEVEL, message, args, **kwargs)


logging.Logger.data = data
logging.Logger.data_debug = data_debug

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
            "encoding": "utf-8",
        },
        # Handler para sinais de trading
        "sinais": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/sinais/sinais_{datetime.now():%d-%m-%Y}.log",
            "formatter": "sinais",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "INFO",
            "encoding": "utf-8",
        },
        # Handler para erros
        "erros": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/erros/erros_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "ERROR",
            "encoding": "utf-8",
        },
        # Novo handler para logs do banco
        "banco": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/banco/banco_{datetime.now():%d-%m-%Y}.log",
            "formatter": "detalhado",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "DATA-DEBUG",  # Inclui DATA e DATA-DEBUG
            "encoding": "utf-8",
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
        # Novo logger específico para banco_dados
        "plugins.banco_dados": {
            "level": "DATA-DEBUG",  # Inclui DATA e DATA-DEBUG
            "handlers": ["banco", "console"],
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


# Executa a configuração se for o ponto de entrada
if __name__ == "__main__":
    configurar_logging()

# fim do arquivo logging_config.py
