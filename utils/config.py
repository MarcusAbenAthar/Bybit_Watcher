# config.py
# Configurações do bot

import os
from dotenv import load_dotenv
import ccxt
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _validar_estilos_sltp(estilos: dict) -> dict:
    """Valida os estilos SLTP para garantir que sl_mult e tp_mult sejam float > 0."""
    estilos_validos = {}
    for nome, params in estilos.items():
        sl_mult = params.get("sl_mult")
        tp_mult = params.get("tp_mult")
        if (
            isinstance(sl_mult, (int, float))
            and sl_mult > 0
            and isinstance(tp_mult, (int, float))
            and tp_mult > 0
        ):
            estilos_validos[nome] = params
        else:
            logger.warning(
                f"Estilo SLTP inválido removido: '{nome}' (sl_mult={sl_mult}, tp_mult={tp_mult})"
            )
    return estilos_validos


def carregar_config() -> dict:
    """Carrega as configurações do bot diretamente do código."""
    load_dotenv()

    # Estilos de SL/TP dinâmicos
    sltp_estilos = {
        "conservador": {"sl_mult": 0.5, "tp_mult": 1.0},
        "moderado": {"sl_mult": 1.0, "tp_mult": 1.5},
        "agressivo": {"sl_mult": 1.5, "tp_mult": 3.0},
    }

    sltp_estilos = _validar_estilos_sltp(sltp_estilos)

    sltp_estilo_padrao = "moderado"
    if sltp_estilo_padrao not in sltp_estilos:
        logger.warning(
            f"Estilo padrão SLTP '{sltp_estilo_padrao}' não encontrado nos estilos. Usando o primeiro disponível."
        )
        sltp_estilo_padrao = next(iter(sltp_estilos), "moderado")

    config = {
        "pares": "XRPUSDT",
        "timeframes": ["1d"],
        "trading": {
            "auto_trade": False,
            "risco_por_operacao": 0.05,
            "alavancagem_maxima": 20,
            "alavancagem_minima": 5,
        },
        "medias_moveis": {
            "periodo_curto": 20,
            "periodo_longo": 50,
        },
        "bybit": {
            "market": "linear",
            "testnet": True,
        },
        "logging": {
            "level": "INFO",
            "debug_enabled": True,
        },
        "sltp_estilos": sltp_estilos,
        "sltp_estilo_padrao": sltp_estilo_padrao,
        "database": {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        },
    }

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
            config["pares"] = ["BTCUSDT"]
    elif isinstance(config["pares"], str):
        config["pares"] = [config["pares"]]

    return config


if __name__ == "__main__":
    config = carregar_config()
