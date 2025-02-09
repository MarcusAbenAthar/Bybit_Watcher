from utils.logging_config import get_logger

logger = get_logger(__name__)
from functools import wraps


def singleton(cls):
    """
    Decorator para implementar o padrão Singleton.

    Args:
        cls: Classe a ser decorada

    Returns:
        Instância única da classe
    """
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
            logger.debug(f"Criada nova instância de {cls.__name__}")
        return instances[cls]

    return get_instance
