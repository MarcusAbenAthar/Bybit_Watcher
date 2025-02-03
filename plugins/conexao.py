from loguru import logger
import ccxt
import os
from plugins.plugin import Plugin


class Conexao(Plugin):
    """
    Plugin para estabelecer e gerenciar a conexão com a Bybit.
    """

    def __init__(self):
        """Inicializa o plugin Conexao."""
        super().__init__()
        self.pares_usdt = []
        self.exchange = None

    def inicializar(self, config=None):
        """
        Estabelece a conexão com a Bybit e carrega apenas os mercados futuros lineares.
        """
        try:
            logger.info("Inicializando a conexão com a Bybit...")

            api_key = os.getenv("BYBIT_API_KEY")
            api_secret = os.getenv("BYBIT_API_SECRET")

            if not api_key or not api_secret:
                raise ValueError("Chaves de API não configuradas corretamente.")

            self.exchange = ccxt.bybit(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "options": {"defaultType": "future"},
                }
            )

            mercados = self.exchange.load_markets()

            if not mercados:
                raise ValueError(
                    "Falha ao carregar os mercados. A resposta veio vazia."
                )

            self.pares_usdt = [
                par
                for par, market in mercados.items()
                if par.endswith("USDT") and market.get("swap") and market.get("linear")
            ]

            if not self.pares_usdt:
                raise ValueError("Nenhum par de futuros lineares USDT encontrado.")

            logger.info(
                f"Conexão estabelecida com sucesso! {len(self.pares_usdt)} pares carregados."
            )
            logger.info(f"Mercado conectado: {self.exchange.options['defaultType']}")

        except Exception as e:
            logger.error(f"Erro ao conectar na Bybit: {e}")
            self.exchange = None
            self.pares_usdt = []
            logger.debug(f"Detalhes do erro: {str(e)}")

            raise
