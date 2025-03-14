"""
Plugin para gerenciamento do banco de dados.

Regras de Ouro:
2 - Criterioso: Validacao rigorosa das operacoes
3 - Seguro: Tratamento de erros 
6 - Clareza: Documentacao clara
7 - Modular: Responsabilidade unica
9 - Testavel: Metodos bem definidos
10 - Documentado: Docstrings completos
"""

import numpy as np
from typing import Optional

from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class BancoDados(Plugin):
    """Plugin para gerenciamento do banco de dados."""

    PLUGIN_NAME = "banco_dados"
    PLUGIN_TYPE = "essencial"

    # Definições das tabelas
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
    }

    def __init__(self, gerenciador_banco):  # Injeção de dependência
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.descricao = "Gerenciamento de banco de dados"
        self._conn = None
        self._config = None
        self.inicializado = False
        self.gerenciador_banco = gerenciador_banco  # Armazena o gerenciador

    def inicializar(self, config: dict) -> bool:
        """Inicializa a conexão com o banco."""
        try:
            if not super().inicializar(config):
                return False

            self._config = config

            # Verifica se o gerenciador existe
            if not self.gerenciador_banco:
                logger.error("Gerenciador de banco não disponível")
                return False

            # Inicializa o gerenciador se necessário
            if not self.gerenciador_banco.inicializado:
                if not self.gerenciador_banco.inicializar(config):
                    logger.error("Falha ao inicializar gerenciador de banco")
                    return False

            # Verifica se o gerenciador tem conexão válida
            if not self.gerenciador_banco._conn:
                logger.error("Gerenciador de banco sem conexão válida")
                return False

            # Usa a conexão do gerenciador
            self._conn = (
                self.gerenciador_banco._conn
            )  # Corrigido: acessando self.gerenciador_banco._conn diretamente
            self.inicializado = True
            logger.info("Banco de dados inicializado com sucesso")
            return True

        except Exception as e:
            logger.exception(f"Erro ao inicializar o banco de dados: {e}")
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
            # Converte valores numéricos para tipos nativos
            if params:
                params = tuple(
                    (
                        float(p)
                        if isinstance(p, np.floating)
                        else int(p) if isinstance(p, np.integer) else p
                    )
                    for p in params
                )

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
            # Verifica se a tabela está definida
            if nome_tabela not in self.TABELAS:
                logger.error(f"Tabela {nome_tabela} não definida")
                return False

            # Verifica se a tabela existe
            tabela_existe = self.executar_query(
                """
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                )
                """,
                (schema, nome_tabela),
            )[0][0]

            # Se a tabela existe, retorna
            if tabela_existe:
                logger.info(f"Tabela {schema}.{nome_tabela} ja existe")
                return True

            # Cria a tabela
            self.executar_query(
                self.TABELAS[nome_tabela].format(schema=schema),
                commit=True,
            )
            logger.info(f"Tabela {schema}.{nome_tabela} criada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar tabela {nome_tabela}: {e}")
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
            # Verifica conexão
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Erro no ciclo de execução: {e}")
            return False

    @property
    def conn(self):
        """
        Retorna a conexão com o banco de dados.

        Returns:
            Connection: Objeto de conexão com o banco de dados
        """
        return self._conn

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
