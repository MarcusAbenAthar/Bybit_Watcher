import importlib
import inspect
import os

from plugins.plugin import Plugin


def carregar_plugins(diretorio, container):  # Recebe o contêiner
    """
    Carrega os plugins do diretório especificado.

    Args:
        diretorio (str): O caminho para o diretório dos plugins.
        container (AppModule): O contêiner de dependências.

    Returns:
        list: Uma lista de instâncias dos plugins carregados.
    """
    plugins = []
    for nome_arquivo in os.listdir(diretorio):
        if nome_arquivo.endswith(".py") and not nome_arquivo.startswith("_"):
            nome_modulo = nome_arquivo[:-3]
            modulo = importlib.import_module(f"plugins.{nome_modulo}")

            for nome, obj in inspect.getmembers(modulo):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Plugin)
                    and obj != Plugin
                    and obj.__name__ != "Plugin"
                    and not any(isinstance(p, obj) for p in plugins)
                ):
                    # Usa o contêiner para instanciar os plugins
                    plugin = container.inject(obj)
                    plugins.append(plugin)

    return plugins
