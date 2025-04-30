import os
import psycopg2

def print_bytes(label, value):
    if value is None:
        print(f"[BYTES] {label}: None")
    else:
        print(f"[BYTES] {label}: {list(value.encode('utf-8', errors='replace'))}")

user = os.getenv("DB_USER")
pwd = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
db = "bybit_watcher_test"
port = os.getenv("DB_PORT")

print("[DEBUG] DB_USER:", user)
print("[DEBUG] DB_PASSWORD:", pwd)
print("[DEBUG] DB_HOST:", host)
print("[DEBUG] DB_NAME:", db)
print("[DEBUG] DB_PORT:", port)

print_bytes("DB_USER", user)
print_bytes("DB_PASSWORD", pwd)
print_bytes("DB_HOST", host)
print_bytes("DB_NAME", db)
print_bytes("DB_PORT", port if port else "")

try:
    conn = psycopg2.connect(
        dbname=db,
        user=user,
        password=pwd,
        host=host,
        port=port,
    )
    print("[OK] Conexão PostgreSQL estabelecida!")
    conn.close()
except Exception as e:
    print("[ERRO] Falha ao conectar:", e)
