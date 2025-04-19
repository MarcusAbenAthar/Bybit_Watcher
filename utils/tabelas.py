# tabelas.py
# Ainda não está pronto, mas já tem uma estrutura básica para criar tabelas no banco de dados PostgreSQL.
# Este arquivo contém a definição de tabelas para armazenar dados de criptomoedas, sinais e indicadores técnicos.

import re
from utils.logging_config import get_logger

logger = get_logger(__name__)


def validar_schema(schema: str) -> str:
    """
    Valida que o schema é um identificador seguro para uso em comandos SQL.

    Args:
        schema (str): Nome do schema a ser validado.

    Returns:
        str: Schema validado ou 'public' se inválido.
    """
    if not schema or not re.match(r"^[a-zA-Z0-9_]+$", schema):
        logger.error(f"Schema inválido: {schema}. Usando 'public' como padrão.")
        return "public"
    return schema


# NOTA: O placeholder {schema} deve ser substituído por um valor validado via validar_schema()
# para evitar injeção de SQL. Exemplo: TABELAS["klines"].format(schema=validar_schema("meu_schema"))
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
            )""",
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
                timestamp BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
    "indicadores_tendencia": """
            CREATE TABLE {schema}.indicadores_tendencia (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                sma REAL,
                ema REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
    "indicadores_osciladores": """
            CREATE TABLE {schema}.indicadores_osciladores (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                rsi REAL,
                stochastic_k REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
    "indicadores_volatilidade": """
            CREATE TABLE {schema}.indicadores_volatilidade (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                atr REAL,
                bollinger_upper REAL,
                bollinger_lower REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
    "indicadores_volume": """
            CREATE TABLE {schema}.indicadores_volume (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                obv REAL,
                vwap REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
    "outros_indicadores": """
            CREATE TABLE {schema}.outros_indicadores (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                tenkan_sen REAL,
                kijun_sen REAL,
                senkou_span_a REAL,
                senkou_span_b REAL,
                fibonacci_50 REAL,
                pivot_point REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, timeframe, timestamp)
            )""",
}
