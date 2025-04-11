"""Gerenciador centralizado de conexões com o banco de dados PostgreSQL."""

from typing import Optional
import psycopg2
from utils.logging_config import get_logger
from plugins.gerenciadores.gerenciadores import BaseGerenciador

logger = get_logger(__name__)


class GerenciadorBanco(BaseGerenciador):
    """Gerenciador de conexões e estruturação do banco."""

    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["banco", "persistencia"]
    PLUGIN_PRIORIDADE = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._conn: Optional[psycopg2.extensions.connection] = None

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com o banco.

        Args:
            config: Configurações de conexão

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if self.inicializado:
                return True

            self._config = config

            if not self._conectar():
                return False

            if not self._criar_tabelas():
                return False

            self.inicializado = True
            logger.info("GerenciadorBanco inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar GerenciadorBanco: {e}", exc_info=True)
            return False

    def _conectar(self) -> bool:
        """Estabelece conexão com o banco."""
        try:
            if self._conn and not self._conn.closed:
                return True

            db_config = self._config.get("database", {})
            self._conn = psycopg2.connect(**db_config)
            logger.debug("Conexão com o banco de dados estabelecida")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return False

    def _criar_tabelas(self) -> bool:
        """Criação de tabelas delegada (vazia por padrão)."""
        logger.warning("Criação de tabelas não implementada")
        return True

    def executar(self, *args, **kwargs) -> tuple[bool, Optional[list]]:
        """
        Executa uma query no banco (CRUD genérico, opcional).

        Args:
            query: String SQL
            params: Tupla com parâmetros (opcional)
            commit: Bool pra confirmar (default=False)

        Returns:
            (True, resultados) ou (False, None)
        """
        logger.warning("Função CRUD não implementada no gerenciador_banco")
        return False, None

    def fechar(self) -> bool:
        """Fecha a conexão com o banco."""
        try:
            if self._conn and not self._conn.closed:
                self._conn.close()
                logger.info("Conexão com o banco fechada")
            return True
        except Exception as e:
            logger.error(f"Erro ao fechar conexão: {e}")
            return False

    @property
    def conn(self):
        """Retorna a conexão ativa (caso necessário externamente)."""
        return self._conn
