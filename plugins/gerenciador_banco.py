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
import time
import sqlite3
from typing import Optional, Tuple, List, Dict
from pathlib import Path

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

from plugins.plugin import Plugin
from utils.singleton import singleton
from utils.logging_config import get_logger

# Constantes
SQLITE_DB = "data/bybit_watcher.db"

logger = get_logger(__name__)


@singleton
class GerenciadorBanco(Plugin):
    """Gerenciador de operações do banco de dados."""

    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self.nome = "gerenciador_banco"
        self.descricao = "Gerenciamento do banco de dados"
        self._pool = None
        self._config = None
        self.inicializado = False
        self._usando_sqlite = False

    def inicializar(self, config: Optional[dict] = None) -> bool:
        """
        Inicializa o gerenciador usando variáveis do .env

        Args:
            config: Configurações opcionais do banco

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            # Inicializa classe base primeiro
            if not super().inicializar(config):
                return False

            # Carrega variáveis do .env
            load_dotenv()

            # Usa config do .env se não fornecida
            if not config:
                config = {
                    "database": {
                        "host": os.getenv("DB_HOST", "localhost"),
                        "database": os.getenv("DB_NAME", "bybit_watcher_db"),
                        "user": os.getenv("DB_USER", "postgres"),
                        "password": os.getenv("DB_PASSWORD", "12345"),
                    }
                }

            self._config = config

            # Cria pool de conexões
            self._criar_pool()
            self.inicializado = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador: {e}")
            return False

    def _verificar_postgresql(self) -> Tuple[bool, str]:
        """
        Verifica se PostgreSQL está disponível e acessível.

        Returns:
            tuple: (disponível, mensagem)
        """
        try:
            # Verifica se PostgreSQL está instalado
            pg_bin = Path("C:/Program Files/PostgreSQL/15/bin")
            if not pg_bin.exists():
                return False, "PostgreSQL não encontrado no caminho padrão"

            # Tenta conectar ao postgres
            conn = psycopg2.connect(
                host=self._config["database"]["host"],
                database="postgres",
                user=self._config["database"]["user"],
                password=self._config["database"]["password"],
                connect_timeout=3,
            )
            conn.close()
            return True, "PostgreSQL disponível"

        except Exception as e:
            return False, f"PostgreSQL não disponível: {e}"

    def _criar_pool(self) -> None:
        """Cria pool de conexões."""
        try:
            if not self._pool:
                # Verifica PostgreSQL
                pg_disponivel, msg = self._verificar_postgresql()
                logger.info(msg)

                if pg_disponivel:
                    # Usa PostgreSQL
                    self._criar_banco_postgres()
                    self._pool = psycopg2.pool.SimpleConnectionPool(
                        minconn=1,
                        maxconn=10,
                        host=self._config["database"]["host"],
                        database=self._config["database"]["database"],
                        user=self._config["database"]["user"],
                        password=self._config["database"]["password"],
                        connect_timeout=5,
                    )
                    logger.info("Pool PostgreSQL criado com sucesso")
                else:
                    # Usa SQLite como fallback
                    logger.info("Usando SQLite como fallback")
                    self._criar_banco_sqlite()
                    self._pool = sqlite3.connect(SQLITE_DB)
                    self._usando_sqlite = True
                    logger.info("Conexão SQLite criada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao criar pool: {e}")
            raise

    def _criar_banco_sqlite(self) -> None:
        """Cria banco SQLite se não existir."""
        try:
            # Garante que o diretório existe
            Path("data").mkdir(exist_ok=True)

            # Conecta ao SQLite (cria o banco se não existir)
            conn = sqlite3.connect(SQLITE_DB)

            # Cria tabelas
            with conn:
                # Tabela de sinais
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sinais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                        timestamp INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_symbol CHECK (symbol LIKE '%USDT')
                    )
                """
                )

                # Índices otimizados
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_sinais_symbol_timeframe ON sinais(symbol, timeframe)",
                    "CREATE INDEX IF NOT EXISTS idx_sinais_timestamp ON sinais(timestamp DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_sinais_confianca ON sinais(confianca DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_sinais_volume ON sinais(volume_24h DESC)"
                ]
                
                for idx in indices:
                    conn.execute(idx)

                # Tabela de análises
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analises (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        tipo_analise TEXT NOT NULL,
                        resultado TEXT NOT NULL,
                        detalhes TEXT,
                        timestamp INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_symbol_analise CHECK (symbol LIKE '%USDT')
                    )
                """
                )

                # Índices para análises
                indices_analise = [
                    "CREATE INDEX IF NOT EXISTS idx_analises_symbol_timeframe ON analises(symbol, timeframe)",
                    "CREATE INDEX IF NOT EXISTS idx_analises_timestamp ON analises(timestamp DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_analises_tipo ON analises(tipo_analise)"
                ]

                for idx in indices_analise:
                    conn.execute(idx)

            logger.info("Banco SQLite criado com sucesso")
            conn.close()

        except Exception as e:
            logger.error(f"Erro ao criar banco SQLite: {e}")
            raise

    def _criar_banco_postgres(self) -> None:
        """Cria o banco PostgreSQL se não existir."""
        try:
            conn = psycopg2.connect(
                host=self._config["database"]["host"],
                database="postgres",
                user=self._config["database"]["user"],
                password=self._config["database"]["password"],
                connect_timeout=3,
            )
            conn.autocommit = True

            with conn.cursor() as cursor:
                # Verifica se o banco existe
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self._config["database"]["database"],),
                )
                if not cursor.fetchone():
                    # Cria o banco
                    cursor.execute(
                        f"CREATE DATABASE {self._config['database']['database']}"
                    )
                    logger.info(f"Banco {self._config['database']['database']} criado")

            conn.close()

        except Exception as e:
            logger.error(f"Erro ao criar banco PostgreSQL: {e}")
            raise

    def executar_query(self, query: str, params: tuple = None, commit: bool = False) -> Optional[list]:
        """
        Executa query no banco de forma segura.

        Args:
            query: Query SQL
            params: Parâmetros da query
            commit: Se True, faz commit da transação

        Returns:
            list: Resultados ou None se erro
        """
        conn = None
        try:
            if self._usando_sqlite:
                conn = self._pool  # SQLite usa conexão direta
            else:
                conn = self._pool.getconn()  # PostgreSQL usa pool

            with conn:
                cur = conn.cursor()
                cur.execute(query, params)
                
                if commit:
                    conn.commit()
                    return []
                    
                if cur.description:
                    return cur.fetchall()
                return []

        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return None

        finally:
            if not self._usando_sqlite and conn:
                self._pool.putconn(conn)

    def salvar_analise(self, symbol: str, timeframe: str, tipo: str, resultado: str, detalhes: str = None) -> bool:
        """
        Salva resultado de uma análise.

        Args:
            symbol: Par analisado
            timeframe: Timeframe da análise
            tipo: Tipo de análise
            resultado: Resultado da análise
            detalhes: Detalhes adicionais (opcional)

        Returns:
            bool: True se salvo com sucesso
        """
        try:
            query = """
                INSERT INTO analises (symbol, timeframe, tipo_analise, resultado, detalhes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (symbol, timeframe, tipo, resultado, detalhes, int(time.time()))
            self.executar_query(query, params, commit=True)
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar análise: {e}")
            return False

    def obter_analises_recentes(self, symbol: str = None, timeframe: str = None, 
                              tipo: str = None, limite: int = 100) -> List[Dict]:
        """
        Obtém análises mais recentes com filtros opcionais.

        Args:
            symbol: Filtrar por par específico
            timeframe: Filtrar por timeframe
            tipo: Filtrar por tipo de análise
            limite: Limite de resultados

        Returns:
            List[Dict]: Lista de análises
        """
        try:
            conditions = ["1=1"]
            params = []

            if symbol:
                conditions.append("symbol = ?")
                params.append(symbol)
            if timeframe:
                conditions.append("timeframe = ?")
                params.append(timeframe)
            if tipo:
                conditions.append("tipo_analise = ?")
                params.append(tipo)

            query = f"""
                SELECT * FROM analises 
                WHERE {' AND '.join(conditions)}
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params.append(limite)

            resultados = self.executar_query(query, tuple(params))
            if not resultados:
                return []

            return [
                {
                    "id": r[0],
                    "symbol": r[1],
                    "timeframe": r[2],
                    "tipo_analise": r[3],
                    "resultado": r[4],
                    "detalhes": r[5],
                    "timestamp": r[6]
                }
                for r in resultados
            ]

        except Exception as e:
            logger.error(f"Erro ao obter análises: {e}")
            return []

    def verificar_conexao(self) -> bool:
        """
        Verifica se conexão está ativa.

        Returns:
            bool: True se conectado
        """
        try:
            self.executar_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar conexão: {e}")
            return False

    def executar(self) -> bool:
        """
        Executa ciclo do plugin.

        Returns:
            bool: True se executado com sucesso
        """
        try:
            return self.verificar_conexao()
        except Exception as e:
            logger.error(f"Erro no ciclo de execução: {e}")
            return False

    def fechar_conexao(self, conn=None):
        """
        Fecha uma conexão específica ou todas as conexões.

        Args:
            conn: Conexão específica a ser fechada. Se None, fecha todas.
        """
        try:
            if self._usando_sqlite:
                if self._pool:
                    self._pool.close()
                    logger.info("Conexão SQLite fechada")
            else:
                if conn:
                    self._pool.putconn(conn)
                    logger.debug("Conexão retornada ao pool")
                elif self._pool:
                    self._pool.closeall()
                    logger.info("Todas as conexões PostgreSQL fechadas")
        except Exception as e:
            logger.error(f"Erro ao fechar conexão: {e}")
            raise

    def finalizar(self):
        """Finaliza o gerenciador."""
        try:
            self.fechar_conexao()
            self._pool = None
            logger.info("Gerenciador de banco finalizado")
        except Exception as e:
            logger.error(f"Erro ao finalizar gerenciador: {e}")