import importlib
import os
import inspect
from loguru import logger
from plugins.plugin import Plugin


def carregar_plugins(diretorio, config):
    """
    Carrega os plugins do diretório especificado.

    Args:
        diretorio (str): O caminho para o diretório dos plugins.
        config (dict): As configurações do bot.

    Returns:
        list: Uma lista de instâncias dos plugins carregados.
    """
    plugins = []
    for nome_arquivo in os.listdir(diretorio):
        if nome_arquivo.endswith(".py") and not nome_arquivo.startswith("_"):
            nome_modulo = nome_arquivo[:-3]
            modulo = importlib.import_module(f"plugins.{nome_modulo}")
            for nome, obj in inspect.getmembers(modulo):
                # Verifica se a classe é uma subclasse de Plugin, se não é a própria classe Plugin e se ainda não foi instanciada
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Plugin)
                    and obj != Plugin
                    and obj.__name__ != "Plugin"
                    and not any(isinstance(p, obj) for p in plugins)
                ):
                    plugin = obj(config)
                    plugins.append(plugin)
    return plugins
