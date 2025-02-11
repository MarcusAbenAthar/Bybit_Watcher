from utils.logging_config import get_logger

logger = get_logger(__name__)
from functools import wraps


class Singleton(type):
    """
    Metaclasse para implementar o padrão Singleton.

    Uso:
        class MinhaClasse(metaclass=Singleton):
            pass
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
