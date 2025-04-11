# config.py
# Configurações fixas do bot, com dados sensíveis carregados do .env

import os
from dotenv import load_dotenv
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Carrega variáveis do .env (apenas informações sensíveis)
load_dotenv()


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
    """Carrega as configurações fixas do sistema + dados sensíveis do .env"""

    sltp_estilos = {
        "conservador": {"sl_mult": 0.5, "tp_mult": 1.0},
        "moderado": {"sl_mult": 1.0, "tp_mult": 1.5},
        "agressivo": {"sl_mult": 1.5, "tp_mult": 3.0},
    }
    sltp_estilos = _validar_estilos_sltp(sltp_estilos)
    sltp_estilo_padrao = "moderado"
    if sltp_estilo_padrao not in sltp_estilos:
        sltp_estilo_padrao = next(iter(sltp_estilos), "moderado")

    config = {
        "pares": ["XRPUSDT"],
        "timeframes": ["1d"],
        "trading": {
            "auto_trade": False,
            "risco_por_operacao": 0.05,
            "alavancagem_maxima": 20,
            "alavancagem_minima": 5,
            "dca_percentual": 0.15,
        },
        "bybit": {
            "api_key": os.getenv("BYBIT_API_KEY"),
            "api_secret": os.getenv("BYBIT_API_SECRET"),
            "market": os.getenv("BYBIT_MARKET", "linear"),
            "testnet": os.getenv("BYBIT_TESTNET", "True").lower() == "true",
        },
        "database": {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        },
        "telegram": {
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        },
        "logging": {
            "level": "INFO",
            "debug_enabled": True,
        },
        "sltp_estilos": sltp_estilos,
        "sltp_estilo_padrao": sltp_estilo_padrao,
    }

    return config


if __name__ == "__main__":
    from pprint import pprint

    pprint(carregar_config())
