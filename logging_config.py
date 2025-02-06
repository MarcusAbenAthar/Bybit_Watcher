"""
Configurações de logging do bot.
Centraliza todas as configurações de logs do sistema.
"""

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        },
        "sinais": {"format": "%(asctime)s | %(levelname)-8s | SINAL: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/bot.log",
            "formatter": "default",
            "level": "DEBUG",
        },
        "sinais": {
            "class": "logging.FileHandler",
            "filename": "logs/sinais.log",
            "formatter": "sinais",
            "mode": "a",
        },
    },
    "loggers": {
        # Core do sistema
        "main": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        # Plugins principais
        "plugins.execucao_ordens": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.medias_moveis": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.sinais_plugin": {
            "handlers": ["console", "sinais"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.calculo_alavancagem": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.analise_candles": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.price_action": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.banco_dados": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.conexao": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # Plugins de indicadores
        "plugins.indicadores.indicadores_tendencia": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.indicadores.indicadores_osciladores": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.indicadores.indicadores_volatilidade": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.indicadores.indicadores_volume": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plugins.indicadores.outros_indicadores": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}
