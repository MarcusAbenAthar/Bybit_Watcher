"""Plugin para operações de gravação no banco de dados.

Segue as regras de ouro:
- Modular, testável, documentado, sem hardcoded.
- Cada plugin declara suas tabelas via `plugin_tabelas`.
- Versionamento obrigatório (plugin_schema_versao).
- Modos de acesso claros (own/write/read).
- Responsabilidade única: operações CRUD simples.
"""

from utils.logging_config import log_banco
from plugins.plugin import Plugin
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import DictCursor
import datetime
import logging
from utils.config import carregar_config
from utils.plugin_utils import validar_klines


class BancoDados(Plugin):
    """
    Plugin para operações básicas de banco de dados.
    Responsabilidade única: operações CRUD simples e registro de tabelas.
    """

    PLUGIN_NAME = "banco_dados"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["banco", "dados", "persistencia"]
    PLUGIN_PRIORIDADE = 100

    def __init__(self, gerenciador_banco=None, **kwargs):
        super().__init__(**kwargs)
        self._gerenciador_banco = gerenciador_banco
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("banco_dados", {}).copy()
            if "plugins" in config and "banco_dados" in config["plugins"]
            else {}
        )
        self._tabelas_registradas = {}
        self._conn = None
        self._cursor = None

    @property
    def plugin_schema_versao(self) -> str:
        """Versão do schema do plugin para controle de migrações."""
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        """
        Define as tabelas do plugin conforme padrão institucional (regras de ouro).
        """
        return {
            "dados": {
                "descricao": "Armazena dados genéricos do sistema, incluindo faixas, contexto e observações.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "chave": "VARCHAR(50) NOT NULL",
                    "valor": "JSONB",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
            "tabelas_registradas": {
                "descricao": "Histórico de tabelas registradas e suas versões.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "tabela": "VARCHAR(50) NOT NULL",
                    "versao": "VARCHAR(10)",
                    "plugin": "VARCHAR(50)",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
            "klines": {
                "descricao": "Armazena candles crus (OHLCV) para cada símbolo/timeframe.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "open": "DECIMAL(18,8)",
                    "high": "DECIMAL(18,8)",
                    "low": "DECIMAL(18,8)",
                    "close": "DECIMAL(18,8)",
                    "volume": "DECIMAL(18,8)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
        }

    @classmethod
    def dependencias(cls):
        """Declara dependências deste plugin."""
        return ["gerenciador_banco"]

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin, valida dependências e registra tabelas.
        """
        try:
            if not super().inicializar(config):
                return False

            if not self._gerenciador_banco:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="gerenciador_banco",
                    operacao="INICIALIZACAO",
                    dados="GerenciadorBanco não foi injetado corretamente",
                    nivel=logging.ERROR,
                )
                return False

            if not self._gerenciador_banco.inicializado:
                if not self._gerenciador_banco.inicializar(config):
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="gerenciador_banco",
                        operacao="INICIALIZACAO",
                        dados="GerenciadorBanco não pôde ser inicializado",
                        nivel=logging.ERROR,
                    )
                    return False

            self._conn = self._gerenciador_banco.conn
            if not self._conn:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="gerenciador_banco",
                    operacao="INICIALIZACAO",
                    dados="Conexão do GerenciadorBanco não foi obtida",
                    nivel=logging.ERROR,
                )
                return False

            self._cursor = self._conn.cursor(cursor_factory=DictCursor)
            if not self._cursor:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="gerenciador_banco",
                    operacao="INICIALIZACAO",
                    dados="Cursor do GerenciadorBanco não foi criado",
                    nivel=logging.ERROR,
                )
                return False
            else:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="gerenciador_banco",
                    operacao="INICIALIZACAO",
                    dados="Cursor do GerenciadorBanco criado com sucesso",
                    nivel=logging.INFO,
                )
            # Registro automático das tabelas do próprio plugin
            for table_name in self.plugin_tabelas.keys():
                try:
                    self.registrar_tabela(self.PLUGIN_NAME, table_name)
                except Exception as e:
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="gerenciador_banco",
                        operacao="INICIALIZACAO",
                        dados=f"Falha ao registrar tabela {table_name}: {e}",
                        nivel=logging.WARNING,
                    )
            return True
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="gerenciador_banco",
                operacao="INICIALIZACAO",
                dados=f"Erro ao inicializar BancoDados: {e}",
                nivel=logging.ERROR,
            )
            return False

    def executar(self, *args, **kwargs) -> bool:
        """Método padrão de execução (não implementa lógica de execução)."""
        log_banco(
            plugin=self.PLUGIN_NAME,
            tabela="gerenciador_banco",
            operacao="EXECUCAO",
            dados="Execução de BancoDados ignorada (sem CRUD implementado)",
            nivel=logging.INFO,
        )
        return True

    def finalizar(self):
        """Finaliza o plugin e fecha o cursor."""
        try:
            if self._cursor:
                self._cursor.close()
            super().finalizar()
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="gerenciador_banco",
                operacao="FINALIZACAO",
                dados="BancoDados finalizado com sucesso",
                nivel=logging.INFO,
            )
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="gerenciador_banco",
                operacao="FINALIZACAO",
                dados=f"Erro ao finalizar BancoDados: {e}",
                nivel=logging.ERROR,
            )

    def registrar_tabela(self, plugin_name: str, table_name: str) -> None:
        """
        Registra uma tabela como pertencente a um plugin.
        Atualiza ou insere registro em tabelas_registradas.
        """
        if plugin_name not in self._tabelas_registradas:
            self._tabelas_registradas[plugin_name] = []
        if table_name not in self._tabelas_registradas[plugin_name]:
            self._tabelas_registradas[plugin_name].append(table_name)
            try:
                if self._cursor:
                    self._cursor.execute(
                        """
                        INSERT INTO tabelas_registradas (nome_tabela, plugin_owner, schema_versao)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (nome_tabela) DO UPDATE SET
                            plugin_owner = EXCLUDED.plugin_owner,
                            schema_versao = EXCLUDED.schema_versao,
                            updated_at = NOW()
                        """,
                        (table_name, plugin_name, self.plugin_schema_versao),
                    )
                    self._conn.commit()
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="tabelas_registradas",
                        operacao="REGISTRO_TABELA",
                        dados=f"Tabela {table_name} registrada para {plugin_name}",
                        nivel=logging.INFO,
                    )
            except Exception as e:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="tabelas_registradas",
                    operacao="REGISTRO_TABELA",
                    dados=f"Erro ao registrar tabela {table_name}: {e}",
                    nivel=logging.ERROR,
                )

    def get_tabelas_por_plugin(self) -> dict:
        """Retorna cópia das tabelas registradas por plugin."""
        return self._tabelas_registradas.copy()

    def inserir(self, tabela: str, dados: Dict[str, Any]) -> bool:
        """
        Insere um registro na tabela especificada.
        """
        try:
            if not self._cursor:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="INSERT",
                    dados="Cursor não inicializado",
                    nivel=logging.ERROR,
                )
                return False

            if not dados:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="INSERT",
                    dados="Dicionário de dados vazio",
                    nivel=logging.ERROR,
                )
                return False

            colunas = list(dados.keys())
            valores = list(dados.values())
            placeholders = ["%s"] * len(colunas)

            query = f"""
                INSERT INTO {tabela} ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            self._cursor.execute(query, valores)
            id_inserido = self._cursor.fetchone()[0]
            self._conn.commit()

            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela=tabela,
                operacao="INSERT",
                dados=f"Registro inserido com ID {id_inserido}",
                nivel=logging.INFO,
            )
            return True
        except Exception as e:
            if self._conn:
                self._conn.rollback()
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="INSERT",
                    dados=f"Erro ao inserir registro: {e}",
                    nivel=logging.ERROR,
                )
            return False

    def buscar(
        self, tabela: str, filtros: Dict[str, Any] = None, limite: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Busca registros na tabela com filtros opcionais.
        """
        try:
            if not self._cursor:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="SELECT",
                    dados="Cursor não inicializado",
                    nivel=logging.ERROR,
                )
                return []

            query = f"SELECT * FROM {tabela}"
            params = []

            if filtros:
                condicoes = [f"{coluna} = %s" for coluna in filtros.keys()]
                params = list(filtros.values())
                query += " WHERE " + " AND ".join(condicoes)

            query += f" LIMIT {limite}"

            self._cursor.execute(query, params)
            resultados = self._cursor.fetchall()

            colunas = [desc[0] for desc in self._cursor.description]
            resultados_dict = [dict(zip(colunas, registro)) for registro in resultados]

            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela=tabela,
                operacao="SELECT",
                dados=f"{len(resultados_dict)} registros encontrados",
                nivel=logging.INFO,
            )
            return resultados_dict
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela=tabela,
                operacao="SELECT",
                dados=f"Erro ao buscar registros: {e}",
                nivel=logging.ERROR,
            )
            return []

    def atualizar(
        self, tabela: str, filtros: Dict[str, Any], dados: Dict[str, Any]
    ) -> bool:
        """
        Atualiza registros na tabela conforme filtros.
        """
        try:
            if not self._cursor:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="UPDATE",
                    dados="Cursor não inicializado",
                    nivel=logging.ERROR,
                )
                return False

            sets = [f"{coluna} = %s" for coluna in dados.keys()]
            wheres = [f"{coluna} = %s" for coluna in filtros.keys()]

            query = f"""
                UPDATE {tabela}
                SET {', '.join(sets)}
                WHERE {' AND '.join(wheres)}
            """

            params = list(dados.values()) + list(filtros.values())
            self._cursor.execute(query, params)
            rows_affected = self._cursor.rowcount
            self._conn.commit()

            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela=tabela,
                operacao="UPDATE",
                dados=f"{rows_affected} registros atualizados",
                nivel=logging.INFO,
            )
            return True
        except Exception as e:
            if self._conn:
                self._conn.rollback()
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="UPDATE",
                    dados=f"Erro ao atualizar registro na tabela {tabela}: {e}",
                    nivel=logging.ERROR,
                )
            return False

    def deletar(self, tabela: str, filtros: Dict[str, Any]) -> bool:
        """
        Deleta registros da tabela conforme filtros.
        """
        try:
            if not self._cursor:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="DELETE",
                    dados="Cursor não inicializado",
                    nivel=logging.ERROR,
                )
                return False

            wheres = [f"{coluna} = %s" for coluna in filtros.keys()]
            query = f"DELETE FROM {tabela} WHERE {' AND '.join(wheres)}"

            self._cursor.execute(query, list(filtros.values()))
            rows_affected = self._cursor.rowcount
            self._conn.commit()

            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela=tabela,
                operacao="DELETE",
                dados=f"{rows_affected} registros deletados",
                nivel=logging.INFO,
            )
            return True
        except Exception as e:
            if self._conn:
                self._conn.rollback()
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela=tabela,
                    operacao="DELETE",
                    dados=f"Erro ao deletar registro na tabela {tabela}: {e}",
                    nivel=logging.ERROR,
                )
            return False

    def inserir_klines(self, klines: List[List], symbol: str, timeframe: str) -> bool:
        """
        Insere múltiplos registros de klines na tabela 'klines'.
        """
        for kline in klines:
            dados = {
                "timestamp": datetime.datetime.fromtimestamp(kline[0] / 1000),
                "symbol": symbol,
                "timeframe": timeframe,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": datetime.datetime.fromtimestamp(kline[6] / 1000),
                "quote_volume": float(kline[7]),
                "trades": int(kline[8]),
                "taker_buy_base": float(kline[9]),
                "taker_buy_quote": float(kline[10]),
            }
            try:
                if not self.inserir("klines", dados):
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="klines",
                        operacao="INSERT",
                        dados=f"Falha ao inserir kline: {dados}",
                        nivel=logging.ERROR,
                    )
                    return False
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="klines",
                    operacao="INSERT",
                    dados=f"Kline inserido: {symbol}, {timeframe}",
                    nivel=logging.INFO,
                )
            except Exception as e:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="klines",
                    operacao="INSERT",
                    dados=f"Erro: {str(e)}, dados={dados}",
                    nivel=logging.ERROR,
                )
                return False
        return True
