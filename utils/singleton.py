import logging
from functools import wraps

logger = logging.getLogger(__name__)


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
