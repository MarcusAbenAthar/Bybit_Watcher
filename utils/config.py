# config.py
# Configurações do bot

import os
from dotenv import load_dotenv
import ccxt
from utils.logging_config import get_logger

logger = get_logger(__name__)


def carregar_config() -> dict:
    """Carrega as configurações do bot diretamente do código."""
    load_dotenv()

    # Configurações fixas
    config = {
        "pares": "BTCUSDT",  # Par padrão ou "All" pra todos os pares
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        "trading": {
            "auto_trade": False,  # Chave on/off pro auto trade
            "risco_por_operacao": 0.01,  # 1% do saldo por operação
            "alavancagem_maxima": 20,  # Máximo de alavancagem
            "alavancagem_minima": 3,  # Mínimo de alavancagem
        },
        "medias_moveis": {
            "periodo_curto": 20,  # Período da MA curta
            "periodo_longo": 50,  # Período da MA longa
        },
        "bybit": {
            "market": "linear",  # Tipo de mercado (futuros perpétuos)
            "testnet": True,  # Usa testnet da Bybit
        },
        "database": {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        },
        "logging": {"level": "INFO"},  # Nível de log padrão
    }

    # Processa os pares
    if config["pares"] == "All":
        try:
            exchange = ccxt.bybit(
                {
                    "apiKey": os.getenv("BYBIT_API_KEY"),
                    "secret": os.getenv("BYBIT_API_SECRET"),
                    "enableRateLimit": True,
                    "options": {"defaultType": config["bybit"]["market"]},
                }
            )
            if config["bybit"]["testnet"]:
                exchange.set_sandbox_mode(True)
            markets = exchange.load_markets()
            config["pares"] = [
                symbol for symbol in markets.keys() if symbol.endswith("/USDT:USDT")
            ]
            logger.info(f"Carregados {len(config['pares'])} pares da Bybit")
        except Exception as e:
            logger.error(f"Erro ao carregar pares da exchange: {e}")
            config["pares"] = ["XRPUSDT"]  # Fallback
    elif isinstance(config["pares"], str):
        config["pares"] = [config["pares"]]

    return config


if __name__ == "__main__":
    # Exemplo de uso
    config = carregar_config()
    print(f"Pares: {config['pares']}")
    print(f"Risco por operação: {config['trading']['risco_por_operacao'] * 100}%")
