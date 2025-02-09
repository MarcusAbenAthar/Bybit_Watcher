"""Inicializador do pacote de plugins."""

from .plugin import Plugin
from .conexao import Conexao
from .banco_dados import BancoDados
from .gerenciador_banco import GerenciadorBanco
from .gerenciador_bot import GerenciadorBot

# Plugins disponíveis
__all__ = ["Plugin", "Conexao", "BancoDados", "GerenciadorBanco", "GerenciadorBot"]
