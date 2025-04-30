"""
SchemaManager: Validação e aplicação do schema.json no banco.
Responsável por garantir que o schema do banco está sincronizado com o JSON.
"""
import json
from pathlib import Path
from utils.logging_config import get_banco_logger
from utils.config import SCHEMA_JSON_PATH
import psycopg2

class SchemaManager:
    """
    Gerencia o schema do banco de dados de acordo com o arquivo schema.json.
    - Valida se o schema atual do banco está sincronizado com o JSON
    - Aplica ajustes automaticamente se necessário
    - Loga todas as operações no logger exclusivo do banco
    """
    def __init__(self, conn):
        self.conn = conn
        self.logger = get_banco_logger()
        self.schema_path = Path(SCHEMA_JSON_PATH)

    def validar_e_aplicar(self):
        if not self.schema_path.exists():
            self.logger.error("schema.json não encontrado!")
            return False
        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        columns = schema.get("columns", {})
        # Salva estado original do autocommit
        old_autocommit = self.conn.autocommit
        self.conn.set_session(autocommit=True)
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'dados'")
                existentes = {row[0] for row in cur.fetchall()}
                for col, tipo in columns.items():
                    if col not in existentes:
                        try:
                            self.logger.info(f"Adicionando coluna {col} ao banco...")
                            cur.execute(f"ALTER TABLE dados ADD COLUMN {col} {tipo}")
                        except Exception as e:
                            self.logger.error(f"Erro ao adicionar coluna {col}: {e}")
                            return False
            self.logger.info("Schema do banco sincronizado com schema.json.")
            return True
        finally:
            self.conn.set_session(autocommit=old_autocommit)
