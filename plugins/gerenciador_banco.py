"""
Plugin para gerenciamento centralizado de conexões com o banco de dados.

Regras de Ouro:
1. Autonomo - Gerencia conexões automaticamente
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros e singleton
4. Certeiro - Operações precisas
5. Eficiente - Pool de conexões
6. Clareza - Bem documentado 
7. Modular - Responsabilidade única
8. Plugins - Interface padronizada
9. Testável - Métodos isolados
10. Documentado - Docstrings completos
"""

import os
from utils.logging_config import get_logger

logger = get_logger(__name__)
import psycopg2
from psycopg2 import pool
from typing import Optional
from dotenv import load_dotenv
from plugins.plugin import Plugin
from utils.singleton import singleton


@singleton
class GerenciadorBanco(Plugin):
    """Gerenciador de operações do banco de dados."""

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self.nome = "gerenciador_banco"
        self.descricao = "Gerenciamento do banco de dados"
        self._pool = None
        self._config = None
        self.inicializado = False

    def inicializar(self, config: Optional[dict] = None) -> bool:
        """
        Inicializa o gerenciador usando variáveis do .env

        Args:
            config: Configurações opcionais do banco

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            # Carrega variáveis do .env
            load_dotenv()

            # Usa config do .env se não fornecida
            if not config:
                config = {
                    "database": {
                        "host": os.getenv("DB_HOST"),
                        "database": os.getenv("DB_NAME"),
                        "user": os.getenv("DB_USER"),
                        "password": os.getenv("DB_PASSWORD"),
                    }
                }

            self._config = config
            self._criar_pool()
            self.inicializado = True
            logger.info("Gerenciador de banco inicializado")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador: {e}")
            return False

    def _criar_pool(self) -> None:
        """Cria pool de conexões."""
        try:
            if not self._pool:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=self._config["database"]["host"],
                    database=self._config["database"]["database"],
                    user=self._config["database"]["user"],
                    password=self._config["database"]["password"],
                    connect_timeout=5,
                )
                logger.info("Pool de conexões criado")

        except Exception as e:
            logger.error(f"Erro ao criar pool: {e}")
            raise

    def executar_query(self, query: str, params: tuple = None) -> Optional[list]:
        """
        Executa query no banco de forma segura.

        Args:
            query: Query SQL
            params: Parâmetros da query

        Returns:
            list: Resultados ou None se erro
        """
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                conn.commit()
                return []

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao executar query: {e}")
            return None

        finally:
            if conn:
                self._pool.putconn(conn)

    def verificar_conexao(self) -> bool:
        """
        Verifica se conexão está ativa.

        Returns:
            bool: True se conectado
        """
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Erro ao verificar conexão: {e}")
            return False
        finally:
            if conn:
                self._pool.putconn(conn)

    def finalizar(self):
        """Finaliza o gerenciador."""
        try:
            if self._pool:
                self._pool.closeall()
                logger.info("Pool de conexões finalizado")
        except Exception as e:
            logger.error(f"Erro ao finalizar pool: {e}")
