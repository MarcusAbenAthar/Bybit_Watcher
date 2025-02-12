import os
from dotenv import load_dotenv


def carregar_config() -> dict:
    """
    Carrega a configuração do bot de forma segura.

    Returns:
        dict: Configuração carregada com timeframes e configurações do banco
    """
    load_dotenv()
    config = {
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        "database": {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        },
    }
    return config
