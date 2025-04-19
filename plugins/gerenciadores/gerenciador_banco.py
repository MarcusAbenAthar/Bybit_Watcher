"""Gerenciador centralizado de conexões com o banco de dados PostgreSQL."""

from typing import Optional, List
from plugins.gerenciadores.gerenciador import BaseGerenciador
import psycopg2
from utils.logging_config import get_logger


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

    def configuracoes_requeridas(self) -> List[str]:
        """
        Retorna lista de chaves obrigatórias no config.

        Returns:
            List[str]: Chaves necessárias no dicionário de configuração.
        """
        return ["database"]

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com o banco.

        Args:
            config: Configurações de conexão com chaves 'database' contendo 'host', 'database', 'user', 'password'.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                return False

            db_config = config.get("database", {})
            chaves_db_requeridas = ["host", "database", "user", "password"]
            if not all(k in db_config for k in chaves_db_requeridas):
                logger.error(
                    f"Configuração de banco incompleta: faltam {chaves_db_requeridas}"
                )
                return False

            if not self._conectar():
                return False

            if not self._criar_tabelas():
                return False

            logger.info("GerenciadorBanco inicializado com sucesso")
            return True
        except KeyError as e:
            logger.error(f"Chave de configuração ausente: {e}")
            return False
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
        except psycopg2.Error as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar: {e}")
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

    def finalizar(self) -> bool:
        """
        Finaliza o gerenciador, fechando a conexão com o banco.

        Returns:
            bool: True se finalizado com sucesso, False caso contrário.
        """
        try:
            self.fechar()
            super().finalizar()
            logger.info("GerenciadorBanco finalizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao finalizar GerenciadorBanco: {e}")
            return False

    def fechar(self) -> bool:
        """Fecha a conexão com o banco."""
        try:
            if self._conn and not self._conn.closed:
                self._conn.close()
                logger.info("Conexão com o banco fechada")
            return True
        except psycopg2.Error as e:
            logger.error(f"Erro ao fechar conexão: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao fechar conexão: {e}")
            return False

    @property
    def conn(self):
        """Retorna a conexão ativa (caso necessário externamente)."""
        return self._conn
