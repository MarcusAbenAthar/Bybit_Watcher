from utils.logging_config import get_logger

logger = get_logger(__name__)
from functools import wraps


def singleton(cls):
    """
    Decorator para garantir que uma classe tenha apenas uma instância.

    Args:
        cls: A classe a ser decorada.

    Returns:
        A instância única da classe.
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance
