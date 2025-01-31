import importlib
import os


def carregar_plugins(diretorio_plugins):
    """Carrega todos os plugins de um determinado diretório.

    Args:
        diretório_plugins (str): Caminho para o diretório onde os plugins estão localizados.

    Returns:
        dict: Um dicionário com o nome do plugin como chave e a classe do plugin como valor.
    """

    plugins = {}
    for filename in os.listdir(diretorio_plugins):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"{diretorio_plugins}.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name in dir(module):
                    if name.startswith("Plugin"):
                        plugin_class = getattr(module, name)
                        plugins[name] = plugin_class
            except Exception as e:
                print(f"Erro ao carregar plugin {filename}: {e}")
    return plugins
