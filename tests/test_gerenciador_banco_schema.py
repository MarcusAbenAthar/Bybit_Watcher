"""
Testes de integração: GerenciadorBanco + SchemaManager + banco real.
Garante que o banco é criado, schema aplicado, e colunas sincronizadas automaticamente.
"""
import os
import psycopg2
import pytest
import json
from pathlib import Path
from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from utils.config import SCHEMA_JSON_PATH

TEST_DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "bybit_watcher_schema_test"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

@pytest.fixture(scope="module")
def conn():
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
    conn = psycopg2.connect(**TEST_DB)
    yield conn
    conn.close()
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
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS dados")
        cur.execute("CREATE TABLE dados (id SERIAL PRIMARY KEY)")
        conn.commit()

def test_gerenciador_banco_schema(tmp_path):
    # Gera um schema.json temporário
    schema = {
        "generated_at": "2025-04-30T13:10:00Z",
        "columns": {"coluna_auto": "FLOAT", "coluna_extra": "INTEGER"}
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    # Monkeypatch o caminho do schema
    from utils import config as config_mod
    orig = config_mod.SCHEMA_JSON_PATH
    config_mod.SCHEMA_JSON_PATH = str(schema_path)
    # Inicializa o GerenciadorBanco, que deve aplicar o schema automaticamente
    config = {"db": TEST_DB}
    gb = GerenciadorBanco()
    assert gb._conectar(TEST_DB)
    # Verifica se as colunas foram criadas
    with gb._conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'dados'")
        cols = {row[0] for row in cur.fetchall()}
        assert "coluna_auto" in cols
        assert "coluna_extra" in cols
    config_mod.SCHEMA_JSON_PATH = orig
