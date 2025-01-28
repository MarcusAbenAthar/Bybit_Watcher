import importlib
import inspect
import os
from plugins.calculo_alavancagem import CalculoAlavancagem
from plugins.plugin import Plugin


def carregar_plugins(diretorio, config, injector):
    """
    Carrega os plugins do diretório especificado.

    Args:
        diretorio (str): O caminho para o diretório dos plugins.
        config (dict): As configurações do bot.
        injector (injector.Injector): O injetor de dependências.

    Returns:
        list: Uma lista de instâncias dos plugins carregados.
    """
    plugins = []
    calculo_alavancagem = injector.get(
        CalculoAlavancagem
    )  # Obtém a instância de CalculoAlavancagem aqui

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
                    plugin = obj(
                        config, calculo_alavancagem
                    )  # Cria a instância do plugin
                    plugins.append(plugin)  # Adiciona o plugin à lista

    return plugins
