from venv import logger
import ccxt
from plugins.plugin import Plugin


def __init__(self):
    """Inicializa o plugin Conexao."""
    super().__init__()


def inicializar(self, config):
    """
    Estabelece a conexão com a Bybit usando o CCXT, utilizando as configurações fornecidas.

    Args:
        config (ConfigParser): Objeto com as configurações do bot.
    """
    try:
        logger.info("Inicializando a conexão com a Bybit...")
        self.exchange = ccxt.bybit(
            {
                "apiKey": config.get(
                    "Bybit", "API_KEY"
                ),  # Obtém as credenciais do config
                "secret": config.get("Bybit", "API_SECRET"),
                "enableRateLimit": True,
            }
        )
        logger.info("Conexão com a Bybit estabelecida com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao conectar na Bybit: {e}")
        raise  # Lança a exceção para tratamento no main.py
