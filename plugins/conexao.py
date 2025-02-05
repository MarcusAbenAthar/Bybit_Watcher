from loguru import logger
import ccxt
import os
from plugins.plugin import Plugin


class Conexao(Plugin):
    """
    Plugin para estabelecer e gerenciar a conexão com a Bybit.
    """

    def __init__(self):
        """
        Inicializa o plugin Conexao.

        Este construtor inicializa uma nova instância da classe `Conexao`.
        Ele define os atributos `pares_usdt` como uma lista vazia e `exchange` como None.
        """
        super().__init__()
        self.pares_usdt = []
        self.exchange = None

    def conectar_bybit(self, api_key, api_secret):
        """
        Conecta à Bybit usando as chaves de API fornecidas.
        """
        try:
            self.exchange = ccxt.bybit(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": "linear",  # Alterado de 'futures' para 'linear'
                        "defaultContractType": "linear",  # Adicionado para especificar futuros lineares
                    },
                }
            )
            logger.info(
                f"Tipo de mercado configurado: {self.exchange.options['defaultType']}"
            )
        except Exception as e:
            logger.error(f"Erro ao conectar na Bybit: {e}")
            raise

    def carregar_mercados(self):
        """
        Carrega os mercados da Bybit.

        Returns:
            Um dicionário contendo os mercados da Bybit.

        Raises:
            ValueError: Se houver algum erro ao carregar os mercados.
        """
        try:
            mercados = self.exchange.load_markets()

            if not mercados:
                raise ValueError(
                    "Falha ao carregar os mercados. A resposta veio vazia."
                )
            return mercados
        except Exception as e:
            logger.error(f"Erro ao carregar os mercados da Bybit: {e}")
            raise

    def filtrar_pares_usdt(self):
        """
        Filtra os pares de moedas USDT dos mercados carregados.
        """
        try:
            # Carrega os mercados
            mercados = self.exchange.load_markets()
            logger.debug(f"Mercados disponíveis: {list(mercados.keys())}")

            # Filtra os pares de moedas USDT
            self.pares_usdt = []
            for market in self.exchange.markets:
                if market.endswith(":USDT"):
                    market_info = self.exchange.markets[market]
                    logger.debug(f"Verificando mercado {market}: {market_info['type']}")
                    if (
                        market_info["type"] == "linear"
                    ):  # Alterado para verificar apenas 'linear'
                        self.pares_usdt.append(market)

            if not self.pares_usdt:
                logger.error("Nenhum par de futuros USDT encontrado após a filtragem")
                raise ValueError("Nenhum symbol de futuros lineares USDT encontrado.")

            logger.info(f"Pares de futuros USDT encontrados: {self.pares_usdt}")

        except Exception as e:
            logger.error(f"Erro ao filtrar os pares de futuros USDT: {e}")
            raise

    def inicializar(self, config=None):
        """
        Inicializa a conexão com a Bybit.

        Este método conecta à Bybit, carrega os mercados e filtra os pares de moedas USDT.

        Args:
            config: Um objeto `ConfigParser` opcional contendo as configurações da Bybit.

        Raises:
            ValueError: Se as chaves de API não forem configuradas corretamente ou se nenhum symbol de futuros lineares USDT for encontrado.
        """
        try:
            logger.info("Inicializando a conexão com a Bybit...")

            api_key = os.getenv("BYBIT_API_KEY")
            api_secret = os.getenv("BYBIT_API_SECRET")

            if not api_key or not api_secret:
                raise ValueError("Chaves de API não configuradas corretamente.")

            self.conectar_bybit(api_key, api_secret)

            self.filtrar_pares_usdt()

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
