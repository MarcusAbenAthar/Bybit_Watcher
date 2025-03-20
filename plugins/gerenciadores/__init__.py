"""
Inicializador do pacote de gerenciadores.
Exporta os gerenciadores disponíveis.
"""

from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin

__all__ = ["GerenciadorBanco", "GerenciadorBot", "GerentePlugin"]


def __init__(self):
    self.plugins = {}
    # Aqui você pode registrar os plugins manualmente ou via um método separado
