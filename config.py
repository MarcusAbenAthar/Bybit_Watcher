LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        },
        "sinais": {"format": "%(asctime)s | %(levelname)-8s | SINAL: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
        "sinais": {
            "class": "logging.FileHandler",
            "filename": "logs/sinais.log",
            "formatter": "sinais",
            "mode": "a",
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO"},
        "plugins.sinais_plugin": {
            "handlers": ["console", "sinais"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
