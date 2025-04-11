"""
Inicializador do pacote de plugins.
Garante que os plugins essenciais e os gerenciadores sejam importados
para que o registro automático via PluginRegistry funcione corretamente.

Nota:
- As dependências entre plugins agora são gerenciadas por plugins_dependencias.json
- O PluginRegistry se encarrega de registrar todos os plugins ao serem importados
"""

# Importa a classe base de plugins e força o carregamento dos essenciais e gerenciadores
from plugins.plugin import Plugin
from plugins.conexao import Conexao
from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.banco_dados import BancoDados
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins

__all__ = [
    "Plugin",
    "Conexao",
    "GerenciadorBanco",
    "BancoDados",
    "GerenciadorBot",
    "GerenciadorPlugins",
]

# Fim do __init__.py
