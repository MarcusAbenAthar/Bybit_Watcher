import logging
import os
import ccxt
from plugins.plugin import Plugin
from utils.singleton import singleton

logger = logging.getLogger(__name__)


@singleton
class Conexao(Plugin):
    """Plugin para conexão com a Bybit."""

    def __init__(self):
        """Inicializa o plugin de conexão."""
        super().__init__()
        self.nome = "Conexão Bybit"
        self.descricao = "Plugin para conexão com a Bybit"
        self._config = None
        self.exchange = None
        self._testnet = True
        self._mercado = "swap"
        self._pares_usdt = []

    def inicializar(self, config):
        """Inicializa a conexão com a Bybit."""
        try:
            logger.info("Inicializando a conexão com a Bybit...")
            if not self._config:
                super().inicializar(config)
                self._config = config
                self._mercado = os.getenv("BYBIT_MARKET", "swap")

                # Conecta à Bybit
                self.conectar_bybit()

                # Filtra pares USDT
                self._pares_usdt = self.filtrar_pares_usdt()

                logger.info("Conexão estabelecida com sucesso!")
                logger.info(f"Mercado conectado: {self._mercado}")

        except Exception as e:
            logger.error(f"Erro ao inicializar conexão: {e}")
            raise

    def validar(self):
        """Valida se a conexão está funcionando."""
        if not self._client:
            raise ValueError("Cliente Bybit não inicializado")
        return True

    def conectar_bybit(self):
        """Estabelece conexão com a Bybit usando variáveis de ambiente."""
        try:
            if not os.getenv("BYBIT_API_KEY") or not os.getenv("BYBIT_API_SECRET"):
                raise ValueError(
                    "Credenciais da Bybit não encontradas nas variáveis de ambiente"
                )

            self.exchange = ccxt.bybit(
                {
                    "apiKey": os.getenv("BYBIT_API_KEY"),
                    "secret": os.getenv("BYBIT_API_SECRET"),
                    "enableRateLimit": True,
                    "options": {"defaultType": self._mercado, "market": "linear"},
                }
            )

            # Configura testnet baseado em variável de ambiente
            self._testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
            if self._testnet:
                self.exchange.set_sandbox_mode(True)
                logger.info("Modo testnet ativado")

            self.exchange.load_markets()
            logger.info("Conexão estabelecida com a Bybit")
            return True

        except Exception as erro:
            logger.error(f"Erro ao conectar na Bybit: {str(erro)}")
            raise

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

            logger.info(f"Total de pares USDT encontrados: {len(pares_usdt)}")
            return pares_usdt

        except Exception as erro:
            logger.error(f"Erro ao filtrar pares USDT: {str(erro)}")
            raise

    def obter_pares_usdt(self):
        """
        Retorna os pares USDT já filtrados.

        Returns:
            list: Lista de pares USDT disponíveis
        """
        return self._pares_usdt

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
