"""
Plugin para gerenciamento centralizado de conexões com o banco de dados.
Implementa o padrão Singleton para garantir uma única conexão durante toda execução.
"""

import logging
from plugins.plugin import Plugin
from plugins.banco_dados import BancoDados

logger = logging.getLogger(__name__)


class GerenciadorBanco(Plugin):
    """
    Gerenciador centralizado de conexões com o banco de dados.
    Implementa o padrão Singleton para garantir uma única conexão.
    """

    _instance = None
    _conexao = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GerenciadorBanco, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.nome = "Gerenciador Banco"
            self.descricao = "Gerenciador de conexão única com banco de dados"
            self.initialized = True
            self._conexao = None

    def get_conexao(self):
        """Retorna a conexão existente ou cria uma nova se necessário."""
        if self._conexao is None and hasattr(self, "_config"):
            self._conexao = self._criar_conexao()
        return self._conexao

    def inicializar(self, config):
        """Inicializa o gerenciador com as configurações."""
        super().inicializar(config)
        try:
            self._config = config
            if self._conexao is None:
                self._conexao = self._criar_conexao()
                logger.info("Conexão com banco de dados estabelecida")
            return self.get_conexao()
        except Exception as e:
            logger.error(f"Erro ao inicializar conexão: {e}")
            raise

    def _criar_conexao(self):
        """Cria uma nova conexão com o banco."""
        try:
            if not self._config:
                raise ValueError("Configuração não inicializada")

            banco = BancoDados(self._config)
            return banco

        except Exception as e:
            logger.error(f"Erro ao criar conexão: {e}")
            raise

    def fechar_conexao(self):
        """Fecha a conexão com o banco."""
        if self._conexao:
            try:
                self._conexao.close()
                self._conexao = None
                logger.info("Conexão com banco de dados encerrada")
            except Exception as e:
                logger.error(f"Erro ao fechar conexão: {e}")


# Instância global única
gerenciador_banco = GerenciadorBanco()
