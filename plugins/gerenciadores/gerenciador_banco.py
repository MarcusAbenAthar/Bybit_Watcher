# gerenciador_banco.py
"""Gerenciador centralizado de conexões com o banco de dados PostgreSQL."""

from utils.logging_config import get_logger
import os
import psycopg2
from dotenv import load_dotenv
from plugins.plugin import Plugin

logger = get_logger(__name__)


class GerenciadorBanco(Plugin):
    """Gerenciador de conexões e inicialização do banco de dados."""

    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_TYPE = "essencial"

    TABELAS = {
        "klines": """
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
            )""",
        "sinais": """
            CREATE TABLE {schema}.sinais (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                tipo TEXT NOT NULL,
                sinal TEXT NOT NULL,
                forca TEXT NOT NULL,
                confianca REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                timestamp BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
        "indicadores_tendencia": """
            CREATE TABLE {schema}.indicadores_tendencia (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                sma REAL,
                ema REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
        "indicadores_osciladores": """
            CREATE TABLE {schema}.indicadores_osciladores (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                rsi REAL,
                stochastic_k REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
        "indicadores_volatilidade": """
            CREATE TABLE {schema}.indicadores_volatilidade (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                atr REAL,
                bollinger_upper REAL,
                bollinger_lower REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
        "indicadores_volume": """
            CREATE TABLE {schema}.indicadores_volume (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                obv REAL,
                vwap REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
        "outros_indicadores": """
            CREATE TABLE {schema}.outros_indicadores (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                tenkan_sen REAL,
                kijun_sen REAL,
                senkou_span_a REAL,
                senkou_span_b REAL,
                fibonacci_50 REAL,
                pivot_point REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
    }

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self._conn = None

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão e cria o banco/tabelas.

        Args:
            config: Configurações do banco (host, database, user, password)

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if not super().inicializar(config):
                return False
            load_dotenv()
            self._config["database"] = {
                "host": config["database"].get("host", os.getenv("DB_HOST")),
                "database": config["database"].get("database", os.getenv("DB_NAME")),
                "user": config["database"].get("user", os.getenv("DB_USER")),
                "password": config["database"].get(
                    "password", os.getenv("DB_PASSWORD")
                ),
            }
            if not self._criar_banco():
                return False
            if not self._conectar():
                return False
            if not self._criar_tabelas():
                return False
            logger.info("GerenciadorBanco inicializado")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar GerenciadorBanco: {e}")
            return False

    def _criar_banco(self) -> bool:
        """Cria o banco de dados se não existir."""
        try:
            conn = psycopg2.connect(
                host=self._config["database"]["host"],
                database="postgres",
                user=self._config["database"]["user"],
                password=self._config["database"]["password"],
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self._config["database"]["database"],),
                )
                if not cur.fetchone():
                    cur.execute(
                        f"CREATE DATABASE \"{self._config['database']['database']}\""
                    )
                    logger.info(f"Banco {self._config['database']['database']} criado")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erro ao criar banco: {e}")
            return False

    def _conectar(self) -> bool:
        """Estabelece conexão com o banco."""
        try:
            self._conn = psycopg2.connect(**self._config["database"])
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return False

    def _criar_tabelas(self) -> bool:
        """Cria tabelas necessárias."""
        try:
            for nome, definicao in self.TABELAS.items():
                with self._conn.cursor() as cur:
                    cur.execute(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s)",
                        (nome,),
                    )
                    if not cur.fetchone()[0]:
                        cur.execute(definicao.format(schema="public"))
                        self._conn.commit()
                        logger.info(f"Tabela {nome} criada")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa uma query no banco.

        Args:
            query: String SQL
            params: Tupla de parâmetros
            commit: Bool pra commitar

        Returns:
            bool: True se executado com sucesso
        """
        query = kwargs.get("query")
        params = kwargs.get("params", ())
        commit = kwargs.get("commit", False)
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                if commit:
                    self._conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return False

    @property
    def conn(self):
        """Retorna a conexão ativa."""
        return self._conn
