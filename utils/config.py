# config.py
# Configurações do bot

import os
from dotenv import load_dotenv


def carregar_config() -> dict:
    load_dotenv()
    config = {
        "pares": "BTCUSDT",  # All para monitorar todos os pares
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        "database": {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        },
    }
    return config
