# logging_config.py
"""Configuração de logging centralizada, segura e dinâmica."""

import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path

# Logger inicial para validação de caminhos
logger = logging.getLogger(__name__)


def validar_caminho_log(caminho: Path) -> Path:
    """
    Valida que o caminho de log é seguro e está dentro do projeto.

    Args:
        caminho (Path): Caminho a ser validado.

    Returns:
        Path: Caminho validado ou padrão 'logs' se inválido.
    """
    projeto_root = Path.cwd()
    caminho_absoluto = caminho.resolve()
    if not str(caminho_absoluto).startswith(str(projeto_root)):
        logger.error(
            f"Caminho de log fora do projeto: {caminho}. Usando padrão 'logs'."
        )
        return projeto_root / "logs"
    return caminho_absoluto


# Caminho base dos logs
LOG_ROOT = validar_caminho_log(Path("logs"))
SUBDIRS = ["bot", "erros", "sinais", "monitoramento"]

# Garante os diretórios de log
for subdir in SUBDIRS:
    (LOG_ROOT / subdir).mkdir(parents=True, exist_ok=True)

# Nome fixo por data
DATA_ATUAL = datetime.now().strftime("%d-%m-%Y")
ARQUIVOS_LOG = {
    "bot": LOG_ROOT / "bot" / f"bot_{DATA_ATUAL}.log",
    "erros": LOG_ROOT / "erros" / f"erros_{DATA_ATUAL}.log",
    "sinais": LOG_ROOT / "sinais" / f"sinais_{DATA_ATUAL}.log",
    "monitoramento": LOG_ROOT / "monitoramento" / f"monitoramento_{DATA_ATUAL}.log",
}

# Nível customizado EXECUÇÃO
EXECUTION_LEVEL = 15
logging.addLevelName(EXECUTION_LEVEL, "EXECUÇÃO")

# Nível customizado MONITORAMENTO
MONITORAMENTO_LEVEL = 21
logging.addLevelName(MONITORAMENTO_LEVEL, "MONITORAMENTO")

def monitoramento(self, message, *args, **kwargs):
    if self.isEnabledFor(MONITORAMENTO_LEVEL):
        self._log(MONITORAMENTO_LEVEL, message, args, **kwargs)

logging.Logger.monitoramento = monitoramento


def execution(self, message, *args, **kwargs):
    if self.isEnabledFor(EXECUTION_LEVEL):
        self._log(EXECUTION_LEVEL, message, args, **kwargs)


logging.Logger.execution = execution

# Formatadores
FORMATADORES = {
    "detalhado": {
        "format": "%(asctime)s | %(levelname)-13s | %(name)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
    "sinais": {
        "format": "%(asctime)s | SINAL | %(filename)s | %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
    "monitoramento": {
        "format": "%(asctime)s | MONITORAMENTO | %(name)s | %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
}

# Handlers de log
HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "detalhado",
        "level": "DEBUG",
    },
    "arquivo": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(ARQUIVOS_LOG["bot"]),
        "formatter": "detalhado",
        "maxBytes": 10 * 1024 * 1024,
        "backupCount": 5,
        "level": "DEBUG",
        "encoding": "utf-8",
    },
    "erros": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(ARQUIVOS_LOG["erros"]),
        "formatter": "detalhado",
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "level": "ERROR",
        "encoding": "utf-8",
    },
    "sinais": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(ARQUIVOS_LOG["sinais"]),
        "formatter": "sinais",
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "level": "INFO",
        "encoding": "utf-8",
    },
    "monitoramento": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(ARQUIVOS_LOG["monitoramento"]),
        "formatter": "monitoramento",
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "level": "MONITORAMENTO",
        "encoding": "utf-8",
    },
    "null": {
        "class": "logging.NullHandler",
    },
}

# Config base (editável)
BASE_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": FORMATADORES,
    "handlers": HANDLERS,
    "loggers": {
        "": {
            "handlers": ["console", "arquivo", "erros"],
            "level": "DEBUG",
            "propagate": False,
        },
        "monitoramento": {
            "handlers": ["monitoramento"],
            "level": "MONITORAMENTO",
            "propagate": False,
        },
        "sinais": {
            "handlers": ["sinais"],
            "level": "DEBUG",
            "propagate": False,
        },
        "ccxt": {"handlers": ["null"], "propagate": False},
        "urllib3": {"handlers": ["null"], "propagate": False},
    },
}

# Flag para garantir que a configuração do logging não seja chamada múltiplas vezes
_logging_configurado = False


def configurar_logging(config: dict = None, debug_enabled: bool = False) -> None:
    """
    Configura o sistema de logging.

    Args:
        config (dict, opcional): Configuração geral do sistema.
        debug_enabled (bool): Se True, ativa logging em nível DEBUG.
    """
    global _logging_configurado
    if _logging_configurado:
        return
    try:
        nivel = logging.DEBUG if debug_enabled else logging.INFO
        BASE_CONFIG["loggers"][""]["level"] = nivel
        BASE_CONFIG["loggers"]["sinais"]["level"] = nivel

        logging.config.dictConfig(BASE_CONFIG)
        logger = logging.getLogger(__name__)
        logger.info(
            f"Logging configurado com nível: {'DEBUG' if debug_enabled else 'INFO'}"
        )
        _logging_configurado = True
    except Exception as e:
        print(f"[FALHA LOGGING] {e}")
        raise


def get_logger(nome: str, debug_enabled=True, monitoramento=False) -> logging.Logger:
    """
    Retorna logger customizado e seguro contra duplicação.

    Args:
        nome (str): Nome do logger.
        debug_enabled (bool): Força nível DEBUG se True.
        monitoramento (bool): Se True, retorna logger para monitoramento.

    Returns:
        logging.Logger
    """
    if monitoramento:
        logger = logging.getLogger("monitoramento")
    else:
        logger = logging.getLogger(nome)
    if not logger.hasHandlers():
        configurar_logging(debug_enabled=debug_enabled)
    return logger
