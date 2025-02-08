import logging

logger = logging.getLogger(__name__)
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
        self.nome = "Conexão"
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

            # Validação dos dados
            for simbolo, dados in mercados.items():
                if dados.get("type") == "swap":
                    ticker = self.exchange.fetch_ticker(simbolo)
                    if ticker["baseVolume"] == 0:
                        logger.warning(f"Volume zero detectado para {simbolo}")

            return mercados
        except Exception as erro:
            logger.error(f"Erro ao carregar mercados: {str(erro)}")
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
        """Filtra e retorna apenas pares USDT Perpetual (Linear)."""
        try:
            mercados = self.exchange.load_markets()
            pares_usdt = []

            for simbolo, dados in mercados.items():
                if (
                    dados.get("type") == "swap"  # Mercado perpétuo
                    and dados.get("quote") == "USDT"  # Par com USDT
                    and dados.get("active")
                ):  # Mercado ativo
                    pares_usdt.append(simbolo)
                    logger.info(f"Par USDT adicionado: {simbolo}")

            logger.info(f"Total de pares USDT encontrados: {len(pares_usdt)}")
            return pares_usdt

        except Exception as erro:
            logger.error(f"Erro ao filtrar pares USDT: {str(erro)}")
            raise

    def validar_mercado(self, dados):
        """
        Valida se um mercado atende aos critérios rigorosos de análise.

        Regras de Ouro aplicadas:
        - Criterioso: Validação rigorosa dos dados
        - Seguro: Checagem de todos os parâmetros
        - Certeiro: Apenas mercados que atendam 100% dos critérios

        Args:
            dados (dict): Dados do mercado da Bybit

        Returns:
            bool: True se o mercado é válido para análise
        """
        try:
            # Validação criteriosa dos dados básicos
            if not all(k in dados for k in ["type", "quote", "active", "baseVolume"]):
                logger.warning("Dados incompletos do mercado")
                return False

            # Regras rigorosas de validação
            regras = {
                "tipo_mercado": dados["type"] == "swap",
                "moeda_quote": dados["quote"] == "USDT",
                "mercado_ativo": dados["active"] is True,
                "volume_minimo": float(dados["baseVolume"])
                > 1000000,  # Volume mínimo 1M USDT
            }

            # Checagem detalhada
            for regra, resultado in regras.items():
                if not resultado:
                    logger.debug(f"Mercado falhou na regra: {regra}")
                    return False

            logger.info(f"Mercado validado com sucesso: {dados['symbol']}")
            return True

        except Exception as erro:
            logger.error(f"Erro na validação do mercado: {str(erro)}")
            return False
