"""
Plugin para gerenciamento centralizado de conexoes com o banco de dados.

Regras de Ouro:
1. Autonomo - Gerencia conexoes automaticamente
2. Criterioso - Validacoes rigorosas
3. Seguro - Tratamento de erros 
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

from utils.logging_config import get_logger

logger = get_logger(__name__)


class GerenciadorBanco(
    Plugin,
):
    """Gerenciador de operacoes do banco de dados."""

    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_TYPE = "essencial"

    # Lista de tabelas padrão
    TABELAS_PADRAO = [
        "klines",
        "sinais",
        "analises",
        "indicadores_tendencia",
        "indicadores_osciladores",
        "indicadores_volatilidade",
        "indicadores_volume",
        "outros_indicadores",
    ]

    # Definições das tabelas
    DEFINICOES_TABELAS = {
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
            )
        """,
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
        "analises": """
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
        "indicadores_tendencia": """
            CREATE TABLE {schema}.indicadores_tendencia (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                sma REAL,
                ema REAL,
                wma REAL,
                dema REAL,
                tema REAL,
                trima REAL,
                kama REAL,
                mama REAL,
                t3 REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )
        """,
        "indicadores_osciladores": """
            CREATE TABLE {schema}.indicadores_osciladores (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                rsi REAL,
                stoch_rsi REAL,
                cci REAL,
                mfi REAL,
                willr REAL,
                ultimate_oscillator REAL,
                stochastic_k REAL,
                stochastic_d REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )
        """,
        "indicadores_volatilidade": """
            CREATE TABLE {schema}.indicadores_volatilidade (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                atr REAL,
                natr REAL,
                trange REAL,
                bollinger_upper REAL,
                bollinger_middle REAL,
                bollinger_lower REAL,
                keltner_upper REAL,
                keltner_middle REAL,
                keltner_lower REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )
        """,
        "indicadores_volume": """
            CREATE TABLE {schema}.indicadores_volume (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                ad REAL,
                adosc REAL,
                obv REAL,
                volume_sma REAL,
                volume_ema REAL,
                vwap REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )
        """,
        "outros_indicadores": """
            CREATE TABLE {schema}.outros_indicadores (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                macd_line REAL,
                macd_signal REAL,
                macd_hist REAL,
                sar REAL,
                adx REAL,
                di_plus REAL,
                di_minus REAL,
                aroon_up REAL,
                aroon_down REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )
        """,
    }

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
                        "host": os.getenv("DB_HOST"),
                        "database": os.getenv("DB_NAME"),
                        "user": os.getenv("DB_USER"),
                        "password": os.getenv("DB_PASSWORD"),
                    }
                }

            self._config = config

            # Conecta ao banco
            if not self._conectar_banco():
                logger.error("Falha na conexão com o banco")
                return False

            # Inicializa schema e tabelas
            if not self._inicializar_schema():
                logger.error("Falha na inicialização do schema")
                return False

            self.inicializado = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador: {e}")
            return False

    def _criar_database(self) -> bool:
        """
        Cria o banco de dados se não existir.

        Returns:
            bool: True se o banco existe ou foi criado com sucesso
        """
        try:
            # Conecta ao postgres para verificar/criar o banco
            conn = psycopg2.connect(
                host=self._config["database"]["host"],
                database="postgres",  # Banco padrão mais estável
                user=self._config["database"]["user"],
                password=self._config["database"]["password"],
                connect_timeout=5,
                client_encoding="LATIN1",
                options="-c client_encoding=LATIN1 -c standard_conforming_strings=on",
            )
            conn.autocommit = True  # Necessário para criar database

            with conn.cursor() as cur:
                # Verifica se o banco existe
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self._config["database"]["database"],),
                )
                exists = cur.fetchone()

                if not exists:
                    # Cria o banco de dados
                    db_name = self._config["database"]["database"]
                    # Escapa o nome do banco para evitar SQL injection
                    cur.execute(
                        f"""
                        CREATE DATABASE "{db_name}"
                        WITH 
                            ENCODING = 'UTF8'
                            LC_COLLATE = 'Portuguese_Brazil.1252'
                            LC_CTYPE = 'Portuguese_Brazil.1252'
                            TEMPLATE template0
                            CONNECTION LIMIT = -1
                        """
                    )
                    logger.info(f"Banco de dados {db_name} criado com sucesso")

            conn.close()
            return True

        except Exception as e:
            logger.error(
                f"Erro na criação do banco de dados: {type(e).__name__} - {str(e)}"
            )
            return False

    def _inicializar_schema(self) -> bool:
        """
        Inicializa o schema e tabelas necessárias.

        Returns:
            bool: True se o schema foi inicializado com sucesso
        """
        try:
            # Cria schema se não existir
            self.executar_query("CREATE SCHEMA IF NOT EXISTS public", commit=True)

            # Cria as tabelas necessárias
            TABELAS_PADRAO = [
                "klines",
                "sinais",
                "analises",
                "indicadores_tendencia",
                "indicadores_osciladores",
                "indicadores_volatilidade",
                "indicadores_volume",
                "outros_indicadores",
            ]

            for tabela in TABELAS_PADRAO:
                if not self.criar_tabela(tabela):
                    logger.error(f"Falha na criação da tabela {tabela}")
                    return False

            return True

        except Exception as e:
            logger.error(
                f"Erro na inicialização do schema: {type(e).__name__} - {str(e)}"
            )
            return False

    def _conectar_banco(self) -> bool:
        """Estabelece conexao com o banco PostgreSQL."""
        try:
            # Primeiro tenta criar o banco se não existir
            if not self._criar_database():
                return False

            # Tenta conectar ao banco
            self._conn = psycopg2.connect(
                host=self._config["database"]["host"],
                database=self._config["database"]["database"],
                user=self._config["database"]["user"],
                password=self._config["database"]["password"],
                connect_timeout=5,
                client_encoding="LATIN1",
                options="-c client_encoding=LATIN1 -c standard_conforming_strings=on",
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
            logger.error(f"Erro na execução da query: {e}")
            return None

    def criar_tabela(self, nome_tabela: str, schema: str = "public") -> bool:
        """
        Cria uma tabela no banco de dados se ela não existir.

        Args:
            nome_tabela: Nome da tabela a ser criada
            schema: Nome do schema onde a tabela será criada

        Returns:
            bool: True se criada com sucesso
        """
        try:
            # Verifica se a tabela já existe
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

            # Se a tabela já existe, retorna
            if exists and exists[0][0]:
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
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

            elif nome_tabela == "sinais":
                self.executar_query(
                    f"""
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
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

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

            elif nome_tabela == "indicadores_tendencia":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.indicadores_tendencia (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        sma REAL,
                        ema REAL,
                        wma REAL,
                        dema REAL,
                        tema REAL,
                        trima REAL,
                        kama REAL,
                        mama REAL,
                        t3 REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

            elif nome_tabela == "indicadores_osciladores":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.indicadores_osciladores (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        rsi REAL,
                        stoch_rsi REAL,
                        cci REAL,
                        mfi REAL,
                        willr REAL,
                        ultimate_oscillator REAL,
                        stochastic_k REAL,
                        stochastic_d REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

            elif nome_tabela == "indicadores_volatilidade":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.indicadores_volatilidade (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        atr REAL,
                        natr REAL,
                        trange REAL,
                        bollinger_upper REAL,
                        bollinger_middle REAL,
                        bollinger_lower REAL,
                        keltner_upper REAL,
                        keltner_middle REAL,
                        keltner_lower REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

            elif nome_tabela == "indicadores_volume":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.indicadores_volume (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        ad REAL,
                        adosc REAL,
                        obv REAL,
                        volume_sma REAL,
                        volume_ema REAL,
                        vwap REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

            elif nome_tabela == "outros_indicadores":
                self.executar_query(
                    f"""
                    CREATE TABLE {schema}.outros_indicadores (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        macd_line REAL,
                        macd_signal REAL,
                        macd_hist REAL,
                        sar REAL,
                        adx REAL,
                        di_plus REAL,
                        di_minus REAL,
                        aroon_up REAL,
                        aroon_down REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (symbol, timeframe, timestamp)
                    )
                    """,
                    commit=True,
                )
                logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
                return True

            # Se chegou aqui, o nome_tabela não corresponde a nenhum caso
            logger.error(f"Nome de tabela não reconhecido: {nome_tabela}")
            return False

        except Exception as e:
            logger.error(f"Erro na criação da tabela {nome_tabela}: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa ciclo do plugin.

        Args:
            *args: Argumentos posicionais ignorados
            **kwargs: Argumentos nomeados ignorados

        Returns:
            bool: True se executado com sucesso
        """
        try:
            # Verifica conexao
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Erro no ciclo de execução: {e}")
            return False

    def finalizar(self):
        """Finaliza o gerenciador."""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
            logger.info("Gerenciador de banco finalizado com sucesso")
        except Exception as e:
            logger.error(f"Erro na finalização do gerenciador: {e}")


def obter_banco_dados(config=None, gerenciador_banco=None):
    """
    Retorna a instância do plugin BancoDados.

    Args:
        config: Configurações do bot
        gerenciador_banco: Instância do gerenciador de banco

    Returns:
        BancoDados: Instância do plugin BancoDados
    """
    from plugins.banco_dados import BancoDados

    # Verifica se temos configuração
    if not config:
        logger.error("Configuração necessária para inicializar banco")
        return None

    # Verifica se o gerenciador existe
    if not gerenciador_banco:
        logger.error("Gerenciador de banco não fornecido")
        return None

    # Inicializa o gerenciador se necessário
    if not gerenciador_banco.inicializado:
        if not gerenciador_banco.inicializar(config):
            logger.error("Falha ao inicializar gerenciador de banco")
            return None

    # Cria e inicializa o banco de dados
    banco = BancoDados(gerenciador_banco)
    if not banco.inicializar(config):
        logger.error("Falha ao inicializar banco de dados")
        return None

    return banco
