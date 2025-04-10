# __init__.py
# # Inicializador do pacote de gerenciadores.
# Exporta os gerenciadores disponíveis.

"""
Inicializador do pacote de gerenciadores.
Exporta os gerenciadores disponíveis.
"""

from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins

__all__ = ["GerenciadorBanco", "GerenciadorBot", "GerenciadorPlugins"]


# fim do __init__.py
