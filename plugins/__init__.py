import importlib
import inspect
import os
from venv import logger

from plugins.plugin import Plugin


def carregar_plugins(diretorio, core):
    plugins = []
    plugins_carregados = {}  # Dicionário para armazenar plugins carregados

    for nome_arquivo in os.listdir(diretorio):
        if nome_arquivo.endswith(".py") and nome_arquivo != "__init__.py":
            nome_modulo = nome_arquivo[:-3]  # Remove a extensão .py
            try:
                modulo = importlib.import_module(f"{diretorio}.{nome_modulo}")
                for nome_classe in dir(modulo):
                    if (
                        nome_classe != "Plugin" and nome_classe[0].isupper()
                    ):  # Verifica se é uma classe de plugin
                        classe_plugin = getattr(modulo, nome_classe)
                        try:
                            plugin = classe_plugin(
                                core
                            )  # Passa a instância do Core para o plugin
                            plugins.append(plugin)
                            plugins_carregados[nome_modulo] = (
                                plugin  # Adiciona o plugin ao dicionário
                            )
                            # Atribui o plugin ao atributo correspondente do Core (exemplo):
                            if nome_modulo == "conexao":
                                core.plugin_conexao = plugin
                            elif nome_modulo == "banco_dados":
                                core.plugin_banco_dados = plugin
                            elif nome_modulo == "medias_moveis":
                                core.plugin_medias_moveis = plugin
                            elif nome_modulo == "calculo_alavancagem":
                                core.plugin_calculo_alavancagem = plugin
                            elif nome_modulo == "price_action":
                                core.plugin_price_action = plugin
                            elif nome_modulo == "execucao_ordens":
                                core.plugin_execucao_ordens = plugin

                        except Exception as e:
                            logger.exception(
                                f"Erro ao instanciar plugin {nome_modulo}: {e}"
                            )
            except ModuleNotFoundError as e:
                logger.exception(f"Erro ao importar módulo {nome_modulo}: {e}")
            except AttributeError as e:
                logger.exception(
                    f"Erro ao carregar classe do módulo {nome_modulo}: {e}"
                )

    return plugins
