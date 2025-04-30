"""Gerenciador centralizado de conexões com o banco de dados PostgreSQL."""

import os
import json
import psycopg2
import psycopg2.extensions
from typing import Optional, List
from pathlib import Path
from utils.config import SCHEMA_JSON_PATH
from utils.logging_config import get_logger
from plugins.gerenciadores.gerenciador import BaseGerenciador

logger = get_logger(__name__)


class GerenciadorBanco(BaseGerenciador):
    PLUGIN_NAME = "gerenciador_banco"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["banco", "persistencia"]
    PLUGIN_PRIORIDADE = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._conn: Optional[psycopg2.extensions.connection] = None

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
        logger.info("GerenciadorBanco inicializado com sucesso")
        return True

    def _validar_config(self, config: dict) -> bool:
        db_cfg = config.get("db", {})
        campos = ["host", "database", "user", "password"]
        faltando = [k for k in campos if not db_cfg.get(k)]
        if faltando:
            logger.error(
                f"Campos de configuração do banco ausentes: {faltando}")
            return False
        return True

    def _conectar(self, db_cfg: dict) -> bool:
        # Configuração de conexão administrativa
        admin_cfg = {
            'host': db_cfg['host'],
            'user': db_cfg['user'],
            'password': db_cfg['password'],
            'dbname': 'postgres'  # Conecta ao banco template
        }
        
        # String de conexão formatada manualmente
        dsn = ""
        for k, v in admin_cfg.items():
            dsn += f"{k}={v} "
        
        # Conexão administrativa com autocommit FORÇADO
        try:
            conn = psycopg2.connect(dsn.strip())
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cur:
                # Verifica existência do banco
                cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db_cfg['database'],))
                if not cur.fetchone():
                    logger.info(f"Criando banco {db_cfg['database']}...")
                    cur.execute(f"CREATE DATABASE {db_cfg['database']} ENCODING 'UTF8'")
                    logger.info("Banco criado com sucesso")
        
        except Exception as e:
            logger.error(f"Falha na criação do banco: {e}", exc_info=True)
            return False
        finally:
            if 'conn' in locals():
                conn.close()

        # Conexão normal ao banco alvo
        try:
            self._conn = psycopg2.connect(**db_cfg)
            return True
        except Exception as e:
            logger.error(f"Falha na conexão principal: {e}")
            return False

    def _garantir_existencia_banco(self, db_cfg: dict):
        dbname = db_cfg["database"]
        admin_cfg = db_cfg.copy()
        admin_cfg["database"] = "postgres"

        original_pgpass = os.environ.get("PGPASSFILE")
        os.environ["PGPASSFILE"] = os.devnull if hasattr(
            os, "devnull") else "nul"

        try:
            with psycopg2.connect(**admin_cfg) as admin_conn:
                admin_conn.set_isolation_level(
                    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                with admin_conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                    if not cur.fetchone():
                        logger.info(f"Criando banco {dbname} automaticamente")
                        cur.execute(
                            f"""
                            CREATE DATABASE {dbname}
                            WITH ENCODING='UTF8'
                            LC_COLLATE='C'
                            LC_CTYPE='C'
                            TEMPLATE=template0;
                            """
                        )

                        logger.info(f"Banco {dbname} criado com sucesso")
        except Exception as e:
            if "CREATE DATABASE não pode ser executado dentro de um bloco de transação" in str(e):
                logger.error(
                    f"Criação automática falhou. Execute manualmente:\n"
                    f"CREATE DATABASE {dbname} WITH ENCODING='UTF8' "
                    f"LC_COLLATE='Portuguese_Brazil.1252' LC_CTYPE='Portuguese_Brazil.1252' TEMPLATE=template0;"
                )
            else:
                logger.error(f"Erro ao garantir banco: {e}", exc_info=True)
        finally:
            if original_pgpass:
                os.environ["PGPASSFILE"] = original_pgpass
            else:
                del os.environ["PGPASSFILE"]

    def _log_erro_encoding(self, dbname, erro):
        logger.error(
            f"[ERRO ENCODING] Conflito de encoding ao acessar o banco {dbname}.\n"
            f"Tente criar manualmente com:\n"
            f"CREATE DATABASE {dbname} WITH ENCODING='UTF8' "
            f"LC_COLLATE='Portuguese_Brazil.1252' LC_CTYPE='Portuguese_Brazil.1252' TEMPLATE=template0;\n"
            f"Detalhe: {erro}"
        )

    def _criar_tabelas(self) -> bool:
        try:
            schema_path = Path(SCHEMA_JSON_PATH)
            if not schema_path.exists():
                logger.error(
                    f"Arquivo de schema não encontrado: {schema_path}")
                return False

            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            
            # Cria tabela padrão 'dados' se não existir no schema
            if "dados" not in schema:
                schema["dados"] = {"columns": {"timestamp": "FLOAT"}}
            
            with self._conn.cursor() as cur:
                # Cria/atualiza todas as tabelas definidas no schema
                for tabela, config in schema.items():
                    columns = config.get("columns", {})
                    if not columns:
                        continue
                        
                    # Cria tabela se não existir
                    col_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
                    cur.execute(f"CREATE TABLE IF NOT EXISTS {tabela} ({col_defs});")
                    
                    # Adiciona colunas faltantes
                    for col, dtype in columns.items():
                        cur.execute(
                            f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {col} {dtype};")
                    
                    # Registra tabela no banco de dados
                    cur.execute("""
                        INSERT INTO tabelas_registradas (nome_tabela, plugin_owner) 
                        VALUES (%s, %s)
                        ON CONFLICT (nome_tabela) DO NOTHING;
                    """, (tabela, config.get("plugin", "system")))
                    
                # Cria tabela de registro de tabelas se não existir
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tabelas_registradas (
                        nome_tabela VARCHAR(255) PRIMARY KEY,
                        plugin_owner VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
            self._conn.commit()
            logger.info(
                f"{len(schema)} tabelas criadas/atualizadas com base em {schema_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}", exc_info=True)
            return False

    def _registrar_em_banco_dados(self):
        try:
            from plugins.banco_dados import BancoDados
            BancoDados.registrar_tabela(BancoDados.PLUGIN_NAME, "dados")
        except Exception as e:
            logger.warning(f"Falha ao registrar tabela em BancoDados: {e}")

    def executar(self, *args, **kwargs) -> tuple[bool, Optional[list]]:
        logger.warning("Função CRUD não implementada no GerenciadorBanco")
        return False, None

    def fechar(self) -> bool:
        try:
            if self._conn and not self._conn.closed:
                self._conn.close()
                logger.info("Conexão com o banco fechada")
            return True
        except Exception as e:
            logger.error(f"Erro ao fechar conexão: {e}")
            return False

    def finalizar(self) -> bool:
        try:
            self.fechar()
            super().finalizar()
            logger.info("GerenciadorBanco finalizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao finalizar GerenciadorBanco: {e}")
            return False

    @property
    def conn(self):
        return self._conn
