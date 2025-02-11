"""
Plugin para gerenciamento do banco de dados.

Regras de Ouro:
2 - Criterioso: Validacao rigorosa das operacoes
3 - Seguro: Tratamento de erros e singleton
6 - Clareza: Documentacao clara
7 - Modular: Responsabilidade unica
9 - Testavel: Metodos bem definidos
10 - Documentado: Docstrings completos
"""

import time
from typing import List, Tuple, Optional
import psycopg2
from utils.singleton import Singleton
from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class BancoDados(Plugin, metaclass=Singleton):
    """Plugin para gerenciamento do banco de dados."""

    # Identificadores do plugin
    PLUGIN_NAME = "banco_dados"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o plugin de banco de dados."""
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.descricao = "Gerenciamento de banco de dados"
        self._conn = None
        self._config = None
        self.inicializado = False

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com o banco.

        Args:
            config (dict): Configurações de conexão

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            # Inicializa classe base
            super().inicializar(config)
            self._config = config

            # Obtém gerenciador de banco com retry
            max_tentativas = 3
            tentativa = 0
            while tentativa < max_tentativas:
                try:
                    from plugins.gerenciadores.gerenciador_plugins import GerentePlugin

                    gerente = GerentePlugin()
                    gerenciador_banco = gerente.plugins.get("gerenciador_banco")

                    if gerenciador_banco and gerenciador_banco.inicializado:
                        # Usa conexão do gerenciador
                        self._conn = gerenciador_banco._conn
                        if self._conn:
                            self.inicializado = True
                            logger.info("Banco de dados inicializado com sucesso")
                            return True

                    tentativa += 1
                    if tentativa < max_tentativas:
                        logger.warning(
                            f"Tentativa {tentativa}: Aguardando gerenciador_banco... (2s)"
                        )
                        time.sleep(2)
                    else:
                        logger.error(
                            "Gerenciador de banco nao disponivel apos tentativas"
                        )
                        return False

                except Exception as e:
                    logger.error(f"Erro ao obter gerenciador_banco: {e}")
                    return False

        except Exception as e:
            logger.error(f"Erro ao inicializar o banco de dados: {e}")
            return False

    def executar_query(
        self, query: str, params: tuple = None, commit: bool = False
    ) -> Optional[list]:
        """
        Executa query no banco de forma segura.

        Args:
            query: Query SQL
            params: Parâmetros da query
            commit: Se True, faz commit da transação

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
            # Verifica conexão
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Erro no ciclo de execução: {e}")
            return False

    def finalizar(self):
        """Finaliza o plugin."""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
            logger.info("Banco de dados finalizado")
        except Exception as e:
            logger.error(f"Erro ao finalizar banco de dados: {e}")


def normalizar_symbol(symbol: str) -> str:
    """
    Normaliza o formato do símbolo para o padrão do banco de dados.

    Args:
        symbol (str): Símbolo no formato original (ex: "BTC/USDT:USDT")

    Returns:
        str: Símbolo normalizado (ex: "BTCUSDT")

    Examples:
        >>> normalizar_symbol("BTC/USDT:USDT")
        'BTCUSDT'
        >>> normalizar_symbol("ETH/USDT")
        'ETHUSDT'
    """
    return symbol.replace("/", "").replace(":USDT", "")
