"""
Plugin para gerenciamento centralizado de conexoes com o banco de dados.

Regras de Ouro:
1. Autonomo - Gerencia conexoes automaticamente
2. Criterioso - Validacoes rigorosas
3. Seguro - Tratamento de erros e singleton
4. Certeiro - Operacoes precisas
5. Eficiente - Performance otimizada
6. Clareza - Bem documentado 
7. Modular - Responsabilidade unica
8. Plugins - Interface padronizada
9. Testavel - Metodos isolados
10. Documentado - Docstrings completos
"""

import os
from typing import Optional, Tuple, List, Dict
import psycopg2
from dotenv import load_dotenv

from plugins.plugin import Plugin
from utils.singleton import Singleton
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GerenciadorBanco(Plugin, metaclass=Singleton):
    """Gerenciador de operacoes do banco de dados."""

    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.descricao = "Gerenciamento do banco de dados"
        self._conn = None
        self._config = None
        self.inicializado = False

    def inicializar(self, config: Optional[dict] = None) -> bool:
        """
        Inicializa o gerenciador usando variaveis do .env

        Args:
            config: Configuracoes opcionais do banco

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            # Inicializa classe base primeiro
            if not super().inicializar(config):
                return False

            # Carrega variaveis do .env
            load_dotenv()

            # Usa config do .env se nao fornecida
            if not config:
                config = {
                    "database": {
                        "host": os.getenv("DB_HOST", "localhost"),
                        "database": os.getenv("DB_NAME", "bybit_watcher"),
                        "user": os.getenv("DB_USER", "postgres"),
                        "password": os.getenv("DB_PASSWORD", "12345"),
                    }
                }

            self._config = config

            # Conecta ao banco
            self._conectar_banco()
            self.inicializado = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador: {e}")
            return False

    def _conectar_banco(self) -> bool:
        """Estabelece conexao com o banco PostgreSQL."""
        try:
            # Tenta conectar ao banco usando caminho absoluto
            import pathlib

            # Tenta conectar ao banco
            self._conn = psycopg2.connect(
                host=self._config["database"]["host"],
                database=self._config["database"]["database"],
                user=self._config["database"]["user"],
                password=self._config["database"]["password"],
                connect_timeout=5,
                client_encoding="utf8",  # Corrigir o encoding
                options="-c client_encoding=utf8",  # Corrigir o encoding
            )
            return True

        except psycopg2.Error as e:
            # Trata erros específicos do PostgreSQL
            logger.error(f"Erro ao conectar ao banco: {e.pgcode} - {e.pgerror}")
            return False
        except Exception as e:
            # Trata outros erros mostrando o tipo do erro
            logger.error(f"Erro ao conectar ao banco: {type(e).__name__} - {str(e)}")
            return False

    def executar_query(
        self, query: str, params: tuple = None, commit: bool = False
    ) -> Optional[list]:
        """
        Executa query no banco de forma segura.

        Args:
            query: Query SQL
            params: Parametros da query
            commit: Se True, faz commit da transacao

        Returns:
            list: Resultados ou None se erro
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)

                if commit:
                    self._conn.commit()
                    return []

                if cur.description:
                    return cur.fetchall()
                return []

        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return None

    def criar_tabela(self, nome_tabela: str, schema: str = "public") -> bool:
        """
        Cria uma tabela no banco de dados se ela nao existir.

        Args:
            nome_tabela: Nome da tabela a ser criada
            schema: Nome do schema onde a tabela sera criada

        Returns:
            bool: True se criada com sucesso
        """
        try:
            # Verifica se a tabela ja existe
            exists = self.executar_query(
                """
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                )
                """,
                (schema, nome_tabela),
            )

            if exists and exists[0][0]:
                logger.info(f"Tabela {schema}.{nome_tabela} ja existe")
                return True

            # Cria a tabela apropriada
            if nome_tabela == "klines":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.klines (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )

            elif nome_tabela == "sinais":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.sinais (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        sinal TEXT NOT NULL,
                        confianca REAL NOT NULL,
                        stop_loss REAL,
                        take_profit REAL,
                        volume_24h REAL,
                        tendencia TEXT,
                        rsi REAL,
                        macd TEXT,
                        suporte REAL,
                        resistencia REAL,
                        timestamp BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )

            elif nome_tabela == "analises":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.analises (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        tipo_analise TEXT NOT NULL,
                        resultado TEXT NOT NULL,
                        detalhes TEXT,
                        timestamp BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )

            logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar tabela {nome_tabela}: {e}")
            return False

    def executar(self) -> bool:
        """
        Executa ciclo do plugin.

        Returns:
            bool: True se executado com sucesso
        """
        try:
            # Verifica conexao
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Erro no ciclo de execucao: {e}")
            return False

    def finalizar(self):
        """Finaliza o gerenciador."""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
            logger.info("Gerenciador de banco finalizado")
        except Exception as e:
            logger.error(f"Erro ao finalizar gerenciador: {e}")
