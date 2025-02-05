from loguru import logger
import ccxt
from dotenv import load_dotenv
import os
from plugins.plugin import Plugin


class Conexao(Plugin):
    """
    Plugin para estabelecer e gerenciar a conexão com a Bybit.
    """

    def __init__(self):
        """
        Inicializa o plugin Conexao.
        """
        super().__init__()
        self.exchange = None
        load_dotenv()

    def conectar_bybit(self, config):
        """
        Estabelece conexão com a Bybit.
        """
        try:
            self.exchange = ccxt.bybit(
                {
                    "apiKey": os.getenv("API_KEY"),
                    "secret": os.getenv("API_SECRET"),
                    "enableRateLimit": True,
                    "options": {"defaultType": "swap", "market": "linear"},
                }
            )

            logger.info(f"Conexão estabelecida com a Bybit")
            return True

        except Exception as erro:
            logger.error(f"Erro ao conectar na Bybit: {str(erro)}")
            return False

    def carregar_mercados(self):
        """
        Carrega os mercados da Bybit.
        """
        try:
            mercados = self.exchange.load_markets()
            return mercados

        except Exception as erro:
            logger.error(f"Erro ao carregar os mercados da Bybit: {str(erro)}")
            raise

    def inicializar(self, config=None):
        """
        Inicializa a conexão com a Bybit.
        """
        try:
            logger.info("Inicializando a conexão com a Bybit...")

            api_key = os.getenv("API_KEY")
            api_secret = os.getenv("API_SECRET")

            if not api_key or not api_secret:
                raise ValueError("Chaves de API não configuradas corretamente.")

            self.conectar_bybit(config)
            self.filtrar_pares_usdt()

            logger.info("Conexão estabelecida com sucesso!")
            logger.info(f"Mercado conectado: {self.exchange.options['defaultType']}")

        except Exception as erro:
            logger.error(f"Erro ao conectar na Bybit: {str(erro)}")
            self.exchange = None
            raise

    def filtrar_pares_usdt(self):
        """
        Loga os pares USDT Perpetual (Linear) disponíveis.
        """
        try:
            mercados = self.exchange.load_markets()

            for simbolo, dados in mercados.items():
                if (
                    dados.get("type") == "swap"
                    and dados.get("settle") == "USDT"
                    and dados.get("linear")
                ):

                    logger.debug(f"Par Perpetual USDT encontrado: {dados['id']}")

        except Exception as erro:
            logger.error(f"Erro ao filtrar os pares USDT: {str(erro)}")
            logger.debug(f"Detalhes do erro: {str(erro)}")
            raise
