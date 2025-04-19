# config.py
# Configurações fixas do bot, com dados sensíveis carregados do .env

import os
from dotenv import load_dotenv
from utils.logging_config import get_logger

logger = get_logger(__name__)
load_dotenv()  # Carrega variáveis sensíveis do .env


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
    """Carrega todas as configurações fixas e sensíveis do sistema."""
    testnet = os.getenv("BYBIT_TESTNET", "True").lower() == "true"

    # Chaves obrigatórias mínimas
    chaves = [
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]

    # Adiciona chaves específicas da Bybit
    if testnet:
        chaves += ["TESTNET_BYBIT_API_KEY", "TESTNET_BYBIT_API_SECRET"]
    else:
        chaves += ["BYBIT_API_KEY", "BYBIT_API_SECRET"]

    # Validação geral das variáveis sensíveis
    for chave in chaves:
        if not os.getenv(chave, "").strip():
            raise ValueError(
                f"Variável de ambiente obrigatória ausente ou vazia: {chave}"
            )

    # Coleta de credenciais da Bybit conforme ambiente
    if testnet:
        api_key = os.getenv("TESTNET_BYBIT_API_KEY")
        api_secret = os.getenv("TESTNET_BYBIT_API_SECRET")
        base_url = "https://api-testnet.bybit.com"
        logger.debug("Credenciais da testnet carregadas.")
    else:
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        base_url = "https://api.bybit.com"
        logger.debug("Credenciais da mainnet carregadas.")

    # Estilos de risco SLTP
    sltp_estilos = _validar_estilos_sltp(
        {
            "conservador": {"sl_mult": 0.5, "tp_mult": 1.0},
            "moderado": {"sl_mult": 1.0, "tp_mult": 1.5},
            "agressivo": {"sl_mult": 1.5, "tp_mult": 3.0},
        }
    )

    sltp_estilo_padrao = (
        "moderado" if "moderado" in sltp_estilos else next(iter(sltp_estilos), None)
    )
    if not sltp_estilo_padrao:
        raise ValueError("Nenhum estilo SLTP válido encontrado.")

    config = {
        "pares": ["BTCUSDT"],
        "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "trading": {
            "auto_trade": False,
            "risco_por_operacao": 0.05,
            "alavancagem_maxima": 20,
            "alavancagem_minima": 5,
            "dca_percentual": 0.15,
        },
        "bybit": {
            "api_key": api_key,
            "api_secret": api_secret,
            "market": os.getenv("BYBIT_MARKET", "linear"),
            "testnet": testnet,
            "base_url": base_url,  # usado direto no conexao.py
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
        "sltp_estilos": sltp_estilos,
        "sltp_estilo_padrao": sltp_estilo_padrao,
    }

    # Validações finais
    if not config["pares"]:
        raise ValueError("A lista de pares não pode ser vazia.")
    if not config["timeframes"]:
        raise ValueError("A lista de timeframes não pode ser vazia.")
    if config["trading"]["risco_por_operacao"] <= 0:
        raise ValueError("O risco_por_operacao deve ser maior que 0.")
    if (
        config["trading"]["alavancagem_maxima"]
        <= config["trading"]["alavancagem_minima"]
    ):
        raise ValueError(
            "A alavancagem_maxima deve ser maior que a alavancagem_minima."
        )
    if config["trading"]["dca_percentual"] <= 0:
        raise ValueError("O dca_percentual deve ser maior que 0.")

    return config


if __name__ == "__main__":
    from pprint import pprint

    pprint(carregar_config())
