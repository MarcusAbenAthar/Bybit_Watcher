# tabelas.py

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
