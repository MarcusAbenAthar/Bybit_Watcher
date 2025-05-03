"""Configuração de logging centralizada, segura e dinâmica."""

import logging
import logging.config
from pathlib import Path
from datetime import datetime

# Logger inicial mínimo para validação
_logger_inicial = logging.getLogger(__name__)


def validar_caminho_log(caminho: Path) -> Path:
    projeto_root = Path.cwd()
    caminho_absoluto = caminho.resolve()
    if not str(caminho_absoluto).startswith(str(projeto_root)):
        _logger_inicial.error(
            f"Caminho de log fora do projeto: {caminho}. Usando padrão 'logs'."
        )
        return projeto_root / "logs"
    return caminho_absoluto


# Caminhos
LOG_ROOT = validar_caminho_log(Path("logs"))
SUBDIRS = ["bot", "erros", "sinais", "banco"]
for subdir in SUBDIRS:
    (LOG_ROOT / subdir).mkdir(parents=True, exist_ok=True)

# Arquivos por data
DATA_ATUAL = datetime.now().strftime("%d-%m-%Y")
ARQUIVOS_LOG = {
    "bot": LOG_ROOT / "bot" / f"bot_{DATA_ATUAL}.log",
    "erros": LOG_ROOT / "erros" / f"erros_{DATA_ATUAL}.log",
    "sinais": LOG_ROOT / "sinais" / f"sinais_{DATA_ATUAL}.log",
    "banco": LOG_ROOT / "banco" / f"banco_{DATA_ATUAL}.log",
}

# Nível customizado
EXECUTION_LEVEL = 15
logging.addLevelName(EXECUTION_LEVEL, "EXECUÇÃO")
logging.Logger.execution = lambda self, msg, *args, **kwargs: (
    self._log(EXECUTION_LEVEL, msg, args, **kwargs)
    if self.isEnabledFor(EXECUTION_LEVEL)
    else None
)

# Formatadores
FORMATADORES = {
    "detalhado": {
        "format": "%(asctime)s | %(levelname)-9s | %(name)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
    "sinais": {
        "format": "%(asctime)s | SINAL | %(filename)s | %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
    "banco": {
        "format": "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
        "datefmt": "%d-%m-%Y %H:%M:%S",
    },
}


# Handler padrão
def _criar_handler_arquivo(
    nome: str, filename: Path, max_mb: int, level: str, formatter: str, tipo="rotativo"
):
    if tipo == "rotativo":
        return {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(filename),
            "formatter": formatter,
            "maxBytes": max_mb * 1024 * 1024,
            "backupCount": 5,
            "level": level,
            "encoding": "utf-8",
        }
    else:  # diário
        return {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(filename),
            "formatter": formatter,
            "when": "midnight",
            "backupCount": 7,
            "encoding": "utf-8",
        }


# Handlers
HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "detalhado",
        "level": "DEBUG",
    },
    "arquivo": _criar_handler_arquivo(
        "arquivo", ARQUIVOS_LOG["bot"], 10, "DEBUG", "detalhado"
    ),
    "erros": _criar_handler_arquivo(
        "erros", ARQUIVOS_LOG["erros"], 5, "ERROR", "detalhado"
    ),
    "sinais": _criar_handler_arquivo(
        "sinais", ARQUIVOS_LOG["sinais"], 5, "INFO", "sinais"
    ),
    "banco": _criar_handler_arquivo(
        "banco", ARQUIVOS_LOG["banco"], 5, "INFO", "banco", tipo="diario"
    ),
    "null": {
        "class": "logging.NullHandler",
    },
}

# Config
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
        "sinais": {
            "handlers": ["sinais"],
            "level": "DEBUG",
            "propagate": False,
        },
        "banco": {
            "handlers": ["banco"],
            "level": "INFO",
            "propagate": False,
        },
        "ccxt": {"handlers": ["null"], "propagate": False},
        "urllib3": {"handlers": ["null"], "propagate": False},
    },
}

_logging_configurado = False


def configurar_logging(config: dict = None, debug_enabled: bool = False) -> None:
    global _logging_configurado
    if _logging_configurado:
        return

    try:
        nivel = logging.DEBUG if debug_enabled else logging.INFO

        # Limpa handlers anteriores
        for logger in [
            logging.getLogger(name) for name in logging.root.manager.loggerDict
        ]:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

        BASE_CONFIG["loggers"][""]["level"] = nivel
        BASE_CONFIG["loggers"]["sinais"]["level"] = nivel

        logging.config.dictConfig(BASE_CONFIG)
        logging.getLogger(__name__).info(
            f"Logging configurado (nível: {'DEBUG' if debug_enabled else 'INFO'})"
        )
        _logging_configurado = True
    except Exception as e:
        raise RuntimeError(f"Falha na configuração de logging: {e}")


def get_logger(nome: str, debug_enabled: bool = True) -> logging.Logger:
    logger = logging.getLogger(nome)
    if not logger.hasHandlers():
        configurar_logging(debug_enabled=debug_enabled)
    return logger


def log_banco(
    plugin: str, tabela: str, operacao: str, dados: str = "", nivel: int = logging.INFO
) -> None:
    """
    Registra logs estruturados para operações de banco de dados.

    Args:
        plugin (str): Nome do plugin (ex.: "banco_dados").
        tabela (str): Nome da tabela (ex.: "dados").
        operacao (str): Tipo de operação (ex.: "INSERT").
        dados (str, optional): Detalhes da operação. Padrão: "".
        nivel (int, optional): Nível de log (ex.: logging.INFO). Padrão: logging.INFO.

    Raises:
        TypeError: Se plugin, tabela, operacao ou dados não forem strings.
        ValueError: Se nivel não for um inteiro.
    """
    # Valida parâmetros obrigatórios
    if not all(isinstance(arg, str) for arg in [plugin, tabela, operacao]):
        raise TypeError("plugin, tabela e operacao devem ser strings")
    if not isinstance(dados, str):
        raise TypeError("dados deve ser uma string")

    # Valida se nivel é um inteiro
    if not isinstance(nivel, int):
        raise ValueError(
            f"nivel deve ser um inteiro, recebido: {type(nivel)} ({nivel})"
        )

    logger = logging.getLogger("banco")
    try:
        # Formata mensagem de log
        log_msg = f"[BANCO] {operacao} na tabela {tabela} | Plugin: {plugin} | Dados: {dados if dados else 'N/A'}"
        logger.log(nivel, log_msg)
    except Exception as e:
        logger.error(f"Falha ao registrar log de banco: {e}", exc_info=True)
