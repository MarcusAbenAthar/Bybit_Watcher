import pytest
import psycopg2
from datetime import datetime
from utils.config import carregar_config
from utils.logging_config import get_logger, log_rastreamento
from plugins.obter_dados import ObterDados
from plugins.conexao import Conexao

"""
Teste real de CRUD no banco 'teste_db', seguindo as regras de ouro:
- Cria e usa o banco 'teste_db' (nunca o banco de produção)
- Cria as tabelas 'klines' (usada pelo teste) e 'teste' (mantém 1 registro para inspeção)
- Limpa apenas a tabela 'klines' ao final
- Logging, rastreabilidade, documentação e segurança
"""

logger = get_logger(__name__)

# Força o uso do banco de testes
DB_NAME = "teste_db"
config = carregar_config()
db_cfg = config["db"].copy()
db_cfg["database"] = DB_NAME
DB_CONFIG = {
    "dbname": DB_NAME,
    "user": db_cfg["user"],
    "password": db_cfg["password"],
    "host": db_cfg["host"],
    "port": int(db_cfg.get("port", 5432)),
}


@pytest.fixture(scope="module")
def conn():
    """
    Fixture de conexão real com o banco 'teste_db', criando-o se não existir.
    Nunca usa o banco de produção. Logging e rastreabilidade completos.
    """
    conn = None
    try:
        logger.info(f"Verificando existência do banco '{DB_NAME}'...")
        admin_cfg = DB_CONFIG.copy()
        admin_cfg["dbname"] = "postgres"
        admin_conn = psycopg2.connect(**admin_cfg)
        admin_conn.autocommit = True
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
            exists = cur.fetchone()
            if not exists:
                logger.info(f"Banco '{DB_NAME}' não existe. Criando...")
                cur.execute(f"CREATE DATABASE {DB_NAME};")
                logger.info(f"Banco '{DB_NAME}' criado com sucesso.")
            else:
                logger.info(f"Banco '{DB_NAME}' já existe.")
        admin_conn.close()
        logger.info(f"Conectando ao banco de dados '{DB_NAME}' para teste CRUD real...")
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except Exception as e:
        logger.error(f"Erro ao conectar/criar banco de dados: {e}")
        pytest.skip(
            f"Banco de dados de teste indisponível ou configuração inválida: {e}"
        )
    finally:
        if conn:
            conn.close()
            logger.info("Conexão com banco de dados de teste encerrada.")


@pytest.fixture(scope="module")
def klines_table(conn):
    """
    Fixture para garantir a existência da tabela 'klines' e limpeza ao final.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS klines (
                id SERIAL PRIMARY KEY,
                timestamp BIGINT NOT NULL,
                open NUMERIC(18,8),
                high NUMERIC(18,8),
                low NUMERIC(18,8),
                close NUMERIC(18,8),
                volume NUMERIC(18,8),
                close_time BIGINT,
                quote_volume NUMERIC(18,8),
                trades INTEGER,
                taker_buy_base NUMERIC(18,8),
                taker_buy_quote NUMERIC(18,8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        logger.info("Tabela 'klines' garantida para o teste.")
    yield
    # Limpa a tabela ao final do módulo
    with conn.cursor() as cur:
        cur.execute("DELETE FROM klines;")
        conn.commit()
        logger.info("Tabela 'klines' limpa após o teste.")


@pytest.fixture(scope="module")
def teste_table(conn):
    """
    Fixture para criar a tabela 'teste' e inserir 1 registro, que permanece ao final.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS teste (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(50) NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        logger.info("Tabela 'teste' garantida para o teste.")
        # Insere 1 registro se a tabela estiver vazia
        cur.execute("SELECT COUNT(*) FROM teste;")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("INSERT INTO teste (nome) VALUES (%s);", ("registro_teste",))
            conn.commit()
            logger.info("Registro inserido na tabela 'teste'.")
    yield
    # Não limpa a tabela 'teste' para inspeção manual


def test_crud_klines_real(conn, klines_table, teste_table):
    """
    Teste institucional de CRUD real na tabela 'klines' usando kline real do plugin ObterDados.
    Também garante a existência da tabela 'teste' com 1 registro para inspeção.
    Cada etapa é rastreada e documentada.
    """
    # Busca um kline real usando o plugin institucional
    symbol = config["ativos"][0] if config["ativos"] else "BTCUSDT"
    timeframe = config["timeframes"][0] if config["timeframes"] else "1h"
    conexao = Conexao()
    assert conexao.inicializar() is True, "Falha ao inicializar conexão institucional."
    plugin_obter = ObterDados(conexao=conexao)
    dados = {}
    plugin_obter.executar(dados, symbol, timeframe, limit=1)
    print(f"Conteúdo retornado por ObterDados: {dados}")
    logger.info(f"Conteúdo retornado por ObterDados: {dados}")
    assert (
        "crus" in dados and len(dados["crus"]) > 0
    ), f"Falha ao obter kline real. Conteúdo de dados: {dados}"
    crus = dados["crus"][0]
    # Preenche campos faltantes se necessário (API pode retornar só 6 colunas)
    while len(crus) < 11:
        crus.append(None)
    logger.info(f"Formato do kline obtido: {crus}")
    kline = {
        "timestamp": crus[0],
        "open": crus[1],
        "high": crus[2],
        "low": crus[3],
        "close": crus[4],
        "volume": crus[5],
        "close_time": crus[6],
        "quote_volume": crus[7],
        "trades": crus[8],
        "taker_buy_base": crus[9],
        "taker_buy_quote": crus[10],
    }
    log_rastreamento(
        componente="test_crud_klines_real",
        acao="obter_kline_real",
        detalhes=f"symbol={symbol}, timeframe={timeframe}, kline={kline}",
    )

    # Inserção
    log_rastreamento(
        componente="test_crud_klines_real", acao="insercao", detalhes=f"dados={kline}"
    )
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO klines (timestamp, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_base, taker_buy_quote)
            VALUES (%(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(close_time)s, %(quote_volume)s, %(trades)s, %(taker_buy_base)s, %(taker_buy_quote)s)
            RETURNING id;
            """,
            kline,
        )
        kline_id = cur.fetchone()[0]
        conn.commit()
    assert kline_id is not None
    log_rastreamento(
        componente="test_crud_klines_real",
        acao="insercao_ok",
        detalhes=f"id={kline_id}",
    )

    # Busca
    log_rastreamento(
        componente="test_crud_klines_real", acao="busca", detalhes=f"id={kline_id}"
    )
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM klines WHERE id = %s;", (kline_id,))
        row = cur.fetchone()
    assert row is not None
    assert row[1] == kline["timestamp"]
    assert float(row[2]) == float(kline["open"])
    assert float(row[3]) == float(kline["high"])
    assert float(row[4]) == float(kline["low"])
    assert float(row[5]) == float(kline["close"])
    log_rastreamento(
        componente="test_crud_klines_real", acao="busca_ok", detalhes=f"row={row}"
    )

    # Deleção
    log_rastreamento(
        componente="test_crud_klines_real", acao="delete", detalhes=f"id={kline_id}"
    )
    with conn.cursor() as cur:
        cur.execute("DELETE FROM klines WHERE id = %s;", (kline_id,))
        conn.commit()
    # Confirma deleção
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM klines WHERE id = %s;", (kline_id,))
        row = cur.fetchone()
    assert row is None
    log_rastreamento(
        componente="test_crud_klines_real", acao="delete_ok", detalhes=f"id={kline_id}"
    )

    # Confirma existência do registro em 'teste'
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM teste;")
        registros = cur.fetchall()
    assert (
        len(registros) >= 1
    ), "A tabela 'teste' deveria conter pelo menos 1 registro para inspeção."
    print(f"Registros atuais na tabela 'teste': {registros}")
    logger.info(f"Registros atuais na tabela 'teste': {registros}")
