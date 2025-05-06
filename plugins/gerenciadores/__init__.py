# __init__.py
# # Inicializador do pacote de gerenciadores.
# Exporta os gerenciadores disponíveis.

"""
Módulo de inicialização dos gerenciadores.
Não deve registrar, inicializar ou finalizar gerenciadores automaticamente.
Apenas expõe utilitários e facilita importações.
Toda a lógica de ciclo de vida dos gerenciadores é centralizada no GerenciadorPlugins.
"""

from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins

__all__ = ["GerenciadorBanco", "GerenciadorBot", "GerenciadorPlugins"]


# fim do __init__.py
