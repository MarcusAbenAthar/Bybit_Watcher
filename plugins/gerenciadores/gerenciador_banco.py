"""Gerenciador centralizado de conexões com o banco de dados PostgreSQL."""

import os
import json
import logging
import psycopg2
import psycopg2.extensions
from typing import Optional, List, TYPE_CHECKING
from pathlib import Path
from utils.config import SCHEMA_JSON_PATH, carregar_config
from utils.logging_config import log_banco
from plugins.gerenciadores.gerenciador import BaseGerenciador
from utils.paths import get_schema_path
from utils.plugin_utils import validar_klines

if TYPE_CHECKING:
    from plugins.plugin import Plugin


class GerenciadorBanco(BaseGerenciador):
    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["banco", "persistencia"]
    PLUGIN_PRIORIDADE = 10
    PLUGIN_VERSION = "1.0"
    PLUGIN_SCHEMA_VERSAO = "1.0"
    PLUGIN_TABELAS = {
        "tabelas_registradas": {
            "columns": {
                "nome_tabela": "VARCHAR(255) PRIMARY KEY",
                "plugin_owner": "VARCHAR(255) NOT NULL",
                "schema_versao": "VARCHAR(20) NOT NULL",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("gerenciadores", {}).get("banco", {}).copy()
            if "gerenciadores" in config and "banco" in config["gerenciadores"]
            else {}
        )
        self._conn: Optional[psycopg2.extensions.connection] = None
        self._plugins: dict = kwargs.get("plugins", {})
        self.inicializado = False

    @classmethod
    def dependencias(cls) -> List[str]:
        return []

    @classmethod
    def identificar_plugins(cls) -> str:
        return cls.PLUGIN_NAME

    def configuracoes_requeridas(self) -> List[str]:
        return ["db"]

    def inicializar(self, config: dict) -> bool:
        if not super().inicializar(config):
            return False

        if not self._validar_config(config):
            return False

        if not self._conectar(config["db"]):
            return False

        if not self._criar_tabelas():
            return False

        self._registrar_em_banco_dados()
        log_banco(
            plugin=self.PLUGIN_NAME,
            tabela="ALL",
            operacao="INIT",
            dados="status: inicializado com sucesso",
        )
        return True

    def _validar_config(self, config: dict) -> bool:
        db_cfg = config.get("db", {})
        campos = ["host", "database", "user", "password"]
        faltando = [k for k in campos if not db_cfg.get(k)]
        if faltando:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="CONFIG_CHECK",
                dados=f"Campos de configuração do banco ausentes: {faltando}",
                nivel=logging.ERROR,
            )
            return False
        return True

    def _conectar(self, db_cfg: dict) -> bool:
        admin_cfg = {
            "host": db_cfg["host"],
            "user": db_cfg["user"],
            "password": db_cfg["password"],
            "dbname": "postgres",
        }

        dsn = ""
        for k, v in admin_cfg.items():
            dsn += f"{k}={v} "

        try:
            conn = psycopg2.connect(dsn.strip())
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (db_cfg["database"],)
                )
                if not cur.fetchone():
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="ALL",
                        operacao="DB_CREATE",
                        dados=f"Criando banco {db_cfg['database']}...",
                    )
                    cur.execute(f"CREATE DATABASE {db_cfg['database']} ENCODING 'UTF8'")
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="ALL",
                        operacao="DB_CREATE",
                        dados="Banco criado com sucesso",
                    )

        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="DB_CREATE",
                dados=f"Falha na criação do banco: {e}",
                nivel=logging.ERROR,
            )
            return False
        finally:
            if "conn" in locals():
                conn.close()

        try:
            self._conn = psycopg2.connect(**db_cfg)
            return True
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="DB_CONNECT",
                dados=f"Falha na conexão principal: {e}",
                nivel=logging.ERROR,
            )
            return False

    def _gerar_schema_inicial(self) -> dict:
        """Gera a estrutura inicial do schema.json"""
        return {
            "schema_versao": "1.0",
            "gerado_por": self.PLUGIN_NAME,
            "tabelas": {
                "dados": {
                    "columns": {
                        "timestamp": "FLOAT",
                        "symbol": "VARCHAR(20)",
                        "price": "FLOAT",
                    },
                    "plugin": "system",
                }
            },
        }

    def _carregar_ou_criar_schema(self) -> dict:
        schema = self._gerar_schema_inicial()

        schema_path = get_schema_path()

        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    loaded_schema = json.load(f)

                if isinstance(loaded_schema, dict) and "tabelas" in loaded_schema:
                    schema.update(loaded_schema)
                else:
                    log_banco(
                        plugin=self.PLUGIN_NAME,
                        tabela="ALL",
                        operacao="SCHEMA_LOAD",
                        dados="Schema inválido - usando estrutura padrão",
                        nivel=logging.WARNING,
                    )

            except Exception as e:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="SCHEMA_LOAD",
                    dados=f"Erro ao carregar schema: {e} - usando estrutura padrão",
                    nivel=logging.ERROR,
                )

        schema.setdefault("tabelas", {})
        return schema

    def _atualizar_schema_com_plugins(self, schema: dict) -> dict:
        """Atualiza o schema com as tabelas declaradas pelos plugins"""
        for plugin_name, plugin in self._plugins.items():
            if hasattr(plugin, "plugin_tabelas"):
                for tabela, cols in plugin.plugin_tabelas.items():
                    if tabela not in schema["tabelas"]:
                        schema["tabelas"][tabela] = {
                            "columns": cols,
                            "plugin": plugin_name,
                            "schema_versao": getattr(
                                plugin, "plugin_schema_versao", "1.0"
                            ),
                        }
                        log_banco(
                            plugin=self.PLUGIN_NAME,
                            tabela=tabela,
                            operacao="SCHEMA_UPDATE",
                            dados=f"Tabela '{tabela}' adicionada ao schema pelo plugin '{plugin_name}'",
                        )
        return schema

    def _criar_tabelas(self) -> bool:
        """Cria/atualiza tabelas baseadas no schema.json"""
        try:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="tabelas_registradas",
                operacao="SCHEMA_CHECK",
                dados=f"Verificando schema versão {self.PLUGIN_VERSION}",
            )

            # Garante que o diretório utils existe
            utils_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "utils"
            )
            os.makedirs(utils_dir, exist_ok=True)

            schema = self._carregar_ou_criar_schema()
            schema = self._atualizar_schema_com_plugins(schema)

            # Salva o schema atualizado
            schema_path = os.path.join(utils_dir, "schema.json")
            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2)

            with self._conn.cursor() as cur:
                # Primeiro cria a tabela de registro se não existir
                self.executar_sql(
                    """
                    CREATE TABLE IF NOT EXISTS tabelas_registradas (
                        nome_tabela VARCHAR(255) PRIMARY KEY,
                        plugin_owner VARCHAR(255) NOT NULL,
                        schema_versao VARCHAR(20) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Depois cria/atualiza as outras tabelas
                for tabela, config in schema["tabelas"].items():
                    try:
                        columns = config.get("columns", {})
                        # Corrigir: se columns contiver 'schema', use apenas columns['schema']
                        if (
                            isinstance(columns, dict)
                            and "schema" in columns
                            and isinstance(columns["schema"], dict)
                        ):
                            columns = columns["schema"]
                        # Se columns contiver 'columns', desaninha
                        if (
                            isinstance(columns, dict)
                            and "columns" in columns
                            and isinstance(columns["columns"], dict)
                        ):
                            columns = columns["columns"]
                        # Remover chaves inválidas
                        for meta in ["schema", "modo_acesso", "plugin"]:
                            if meta in columns:
                                log_banco(
                                    plugin=self.PLUGIN_NAME,
                                    tabela=tabela,
                                    operacao="SCHEMA_CHECK",
                                    dados=f"Removendo chave inválida '{meta}' de columns da tabela '{tabela}'",
                                    nivel=logging.WARNING,
                                )
                                columns.pop(meta)
                        if not columns or not isinstance(columns, dict):
                            log_banco(
                                plugin=self.PLUGIN_NAME,
                                tabela=tabela,
                                operacao="SCHEMA_CHECK",
                                dados=f"Tabela '{tabela}' ignorada: columns inválido ou vazio.",
                                nivel=logging.WARNING,
                            )
                            continue
                        existe = self.executar_sql(
                            """
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' AND table_name = %s
                            );
                            """,
                            (tabela,),
                            fetchone=True,
                        )
                        tabela_existe = existe[0] if existe else False
                        if not tabela_existe:
                            col_defs = ", ".join(
                                f"{col} {dtype}" for col, dtype in columns.items()
                            )
                            self.executar_sql(
                                f"CREATE TABLE IF NOT EXISTS {tabela} ({col_defs});"
                            )
                        else:
                            for col, dtype in columns.items():
                                try:
                                    self.executar_sql(
                                        f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {col} {dtype};"
                                    )
                                except Exception as e:
                                    log_banco(
                                        plugin=self.PLUGIN_NAME,
                                        tabela=tabela,
                                        operacao="SCHEMA_CHECK",
                                        dados=f"Erro ao adicionar coluna {col} na tabela {tabela}: {e}",
                                        nivel=logging.WARNING,
                                    )
                                    continue
                        self.executar_sql(
                            """
                            INSERT INTO tabelas_registradas 
                            (nome_tabela, plugin_owner, schema_versao, updated_at)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (nome_tabela) DO UPDATE SET
                                plugin_owner = EXCLUDED.plugin_owner,
                                schema_versao = EXCLUDED.schema_versao,
                                updated_at = NOW();
                            """,
                            (
                                tabela,
                                config.get("plugin", "system"),
                                config.get("schema_versao", "1.0"),
                            ),
                        )
                    except Exception as e:
                        log_banco(
                            plugin=self.PLUGIN_NAME,
                            tabela=tabela,
                            operacao="SCHEMA_CHECK",
                            dados=f"Erro ao processar tabela {tabela}: {e}",
                            nivel=logging.ERROR,
                        )
                        continue

                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="SCHEMA_CHECK",
                    dados=f"{len(schema['tabelas'])} tabelas criadas/atualizadas",
                )
                return True

        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="SCHEMA_CHECK",
                dados=f"Erro ao criar tabelas: {e}",
                nivel=logging.ERROR,
            )
            if self._conn:
                self._conn.rollback()
            return False

    def registrar_tabela(self, plugin_name: str, table_name: str, schema: dict) -> bool:
        """
        Registra uma nova tabela no banco de dados.

        Args:
            plugin_name (str): Nome do plugin que está registrando a tabela
            table_name (str): Nome da tabela a ser registrada
            schema (dict): Schema da tabela com colunas e tipos

        Returns:
            bool: True se registrado com sucesso, False caso contrário
        """
        try:
            banco_dados = self._gerente.obter_plugin("banco_dados")
            if not banco_dados:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="REGISTER_TABLE",
                    dados="Plugin banco_dados não encontrado",
                    nivel=logging.ERROR,
                )
                return False

            sucesso = banco_dados.registrar_tabela(table_name, schema)
            if sucesso:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="REGISTER_TABLE",
                    dados=f"Tabela {table_name} registrada com sucesso",
                )
            else:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="REGISTER_TABLE",
                    dados=f"Falha ao registrar tabela {table_name}",
                    nivel=logging.ERROR,
                )
            return sucesso

        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="REGISTER_TABLE",
                dados=f"Erro ao registrar tabela {table_name}: {e}",
                nivel=logging.ERROR,
            )
            return False

    def _registrar_em_banco_dados(self):
        try:
            from plugins.banco_dados import BancoDados

            banco_dados = BancoDados(gerenciador_banco=self)
            banco_dados.registrar_tabela(BancoDados.PLUGIN_NAME, "dados")
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="REGISTER_TABLE",
                dados=f"Falha ao registrar tabela em BancoDados: {e}",
                nivel=logging.WARNING,
            )

    def validar_schema_plugin(self, plugin: "Plugin") -> bool:
        from utils.schema_generator import validar_plugin_tabelas

        if not validar_plugin_tabelas(plugin):
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="SCHEMA_CHECK",
                dados=f"Schema inválido para o plugin {plugin.nome}",
                nivel=logging.ERROR,
            )
            return False
        return True

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa operações no banco de dados.

        Returns:
            bool: True se a operação foi bem sucedida, False caso contrário.
        """
        try:
            if not self.inicializado:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="EXECUTE",
                    dados="GerenciadorBanco não inicializado",
                    nivel=logging.ERROR,
                )
                return False

            if not self._conn or self._conn.closed:
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="EXECUTE",
                    dados="Conexão com banco não está ativa",
                    nivel=logging.ERROR,
                )
                return False

            return True
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="EXECUTE",
                dados=f"Erro na execução: {e}",
                nivel=logging.ERROR,
            )
            return False

    def fechar(self) -> bool:
        try:
            if self._conn and not self._conn.closed:
                self._conn.close()
                log_banco(
                    plugin=self.PLUGIN_NAME,
                    tabela="ALL",
                    operacao="DB_CLOSE",
                    dados="Conexão com o banco fechada",
                )
            return True
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="DB_CLOSE",
                dados=f"Erro ao fechar conexão: {e}",
                nivel=logging.ERROR,
            )
            return False

    def finalizar(self) -> bool:
        try:
            self.fechar()
            super().finalizar()
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="FINALIZE",
                dados="GerenciadorBanco finalizado com sucesso",
            )

            return True
        except Exception as e:
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="FINALIZE",
                dados=f"Erro ao finalizar GerenciadorBanco: {e}",
                nivel=logging.ERROR,
            )
            return False

    @property
    def conn(self):
        return self._conn

    def executar_sql(self, query, params=None, fetchone=False, fetchall=False):
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                if fetchone:
                    result = cur.fetchone()
                elif fetchall:
                    result = cur.fetchall()
                else:
                    result = None
                self._conn.commit()
                return result
        except Exception as e:
            if self._conn:
                self._conn.rollback()
            log_banco(
                plugin=self.PLUGIN_NAME,
                tabela="ALL",
                operacao="SQL_EXEC",
                dados=f"Erro ao executar SQL: {e} | Query: {query}",
                nivel=logging.ERROR,
            )
            raise

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "tabelas_registradas": {
                "descricao": "Histórico de tabelas registradas, plugins responsáveis, versões e rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "nome_tabela": "VARCHAR(255) PRIMARY KEY",
                    "plugin_owner": "VARCHAR(255) NOT NULL",
                    "schema_versao": "VARCHAR(20) NOT NULL",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "detalhes": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
