"""
Inicializador dinâmico dos plugins.

Importa automaticamente todos os módulos dentro de plugins/, exceto os explicitamente ignorados.
Registra automaticamente todas as subclasses de Plugin e BaseGerenciador.

Regras:
- Varre recursivamente a pasta plugins/
- Ignora arquivos "__init__.py", "__pycache__", "plugin.py", "gerenciadores.py"
"""

import importlib
import pkgutil
import pathlib

from plugins.plugin import Plugin, PluginRegistry
from plugins.gerenciadores.gerenciadores import BaseGerenciador

__all__ = ["Plugin", "PluginRegistry", "BaseGerenciador"]

# Caminho base do pacote plugins/
base_path = pathlib.Path(__file__).parent
package_root = __name__  # Geralmente 'plugins'

# Módulos a serem ignorados durante a importação
IGNORAR = {"__init__.py", "__pycache__", "plugin.py", "gerenciadores.py"}


def _importar_modulos_recursivamente():
    for finder, name, ispkg in pkgutil.walk_packages(
        path=[str(base_path)], prefix=f"{package_root}.", onerror=lambda x: None
    ):
        nome_modulo = name.split(".")[-1]
        if nome_modulo in IGNORAR:
            continue
        try:
            importlib.import_module(name)
        except Exception as e:
            print(f"[IMPORT WARNING] Erro ao importar módulo '{name}': {e}")


# Dispara a varredura e importação
_importar_modulos_recursivamente()
