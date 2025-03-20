# Esse é o __init__.py do pacote de plugins.
# Ele é responsável por inicializar o pacote e garantir que os plugins sejam carregados corretamente.

"""
Inicializador do pacote de plugins.
Exporta os plugins disponíveis e garante que sejam carregados corretamente.

Ordem de dependências:
1. conexao (sem dependências)
2. gerenciador_banco (sem dependências)
3. banco_dados (depende de gerenciador_banco)
4. gerenciador_bot (depende de banco_dados e gerenciador_banco)
"""

# Importa classe base primeiro
from plugins.plugin import Plugin

# Plugins essenciais em ordem de dependência
from plugins.conexao import Conexao  # Sem dependências
from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco  # Sem dependências
from plugins.banco_dados import BancoDados  # Depende de gerenciador_banco
from plugins.gerenciadores.gerenciador_bot import (
    GerenciadorBot,
)  # Depende de banco_dados e gerenciador_banco

# Exporta as classes para serem encontradas pelo gerente de plugins
__all__ = [
    # Plugins essenciais em ordem de dependência
    "Plugin",  # Base
    "Conexao",  # Sem dependências
    "GerenciadorBanco",  # Sem dependências
    "BancoDados",  # Depende de gerenciador_banco
    "GerenciadorBot",  # Depende de banco_dados e gerenciador_banco
]

# Registra plugins disponíveis em ordem de dependência
available_plugins = {
    # Plugins essenciais
    "conexao": Conexao,  # Sem dependências
    "gerenciador_banco": GerenciadorBanco,  # Sem dependências
    "banco_dados": BancoDados,  # Depende de gerenciador_banco
    "gerenciador_bot": GerenciadorBot,  # Depende de banco_dados e gerenciador_banco
}
