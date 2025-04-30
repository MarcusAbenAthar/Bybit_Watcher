"""
Testes unitários para SchemaManager.
"""
import os
import psycopg2
import pytest
import json
from pathlib import Path
from utils.schema_manager import SchemaManager
from utils.config import SCHEMA_JSON_PATH

# Configuração de teste (ajuste conforme seu ambiente de test)
TEST_DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "bybit_watcher_test"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

@pytest.fixture(scope="module")
def conn():
    # Cria banco de teste se não existir
    admin_cfg = TEST_DB.copy()
    admin_cfg["database"] = "postgres"
    admin_conn = psycopg2.connect(**admin_cfg)
    admin_conn.set_session(autocommit=True)
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB['database']}'")
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {TEST_DB['database']} WITH ENCODING='UTF8';")
    finally:
        admin_conn.close()
    # Conecta ao banco de teste
    conn = psycopg2.connect(**TEST_DB)
    yield conn
    conn.close()
    # Limpeza: drop do banco de teste
    admin_conn = psycopg2.connect(**admin_cfg)
    admin_conn.set_session(autocommit=True)
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{TEST_DB['database']}' AND pid <> pg_backend_pid();")
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB['database']};")
    finally:
        admin_conn.close()

@pytest.fixture(autouse=True)
def setup_schema(conn):
    # Cria tabela dummy para testes
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS dados")
        cur.execute("CREATE TABLE dados (id SERIAL PRIMARY KEY)")
        conn.commit()


def test_schema_manager_adiciona_colunas(conn, tmp_path):
    # Gera um schema.json temporário
    schema = {
        "generated_at": "2025-04-30T13:00:00Z",
        "columns": {"campo_teste": "FLOAT", "campo_extra": "INTEGER"}
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    # Monkeypatch o caminho do schema
    orig = SCHEMA_JSON_PATH
    try:
        import utils.schema_manager as sm_mod
        sm_mod.SCHEMA_JSON_PATH = str(schema_path)
        manager = SchemaManager(conn)
        assert manager.validar_e_aplicar() is None or manager.validar_e_aplicar() is True
        # Verifica se as colunas foram criadas
        with conn.cursor() as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'dados'")
            cols = {row[0] for row in cur.fetchall()}
            assert "campo_teste" in cols
            assert "campo_extra" in cols
    finally:
        sm_mod.SCHEMA_JSON_PATH = orig
