# conexao.py
"""Plugin para conexão com a API da Bybit."""

from utils.logging_config import get_logger
import os
import ccxt
from plugins.plugin import Plugin

logger = get_logger(__name__)


class Conexao(Plugin):
    """Classe para gerenciar a conexão com a Bybit."""

    PLUGIN_NAME = "conexao"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):  # Adicionado 'gerente' como opcional
        """
        Inicializa o plugin de conexão.

        Args:
            gerente: Instância do GerentePlugin (opcional, injetado pelo GerentePlugin)
        """
        super().__init__()
        self.exchange = None
        self._mercado = os.getenv("BYBIT_MARKET", "linear")
        self._pares_usdt = []
        self._gerente = gerente  # Armazena se fornecido, mas não é usado aqui

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com a Bybit usando credenciais do ambiente.

        Args:
            config: Dicionário de configurações do bot

        Returns:
            bool: True se inicializado com sucesso, False caso contrário
        """
        try:
            if not super().inicializar(config):
                return False
            api_key = os.getenv("BYBIT_API_KEY")
            api_secret = os.getenv("BYBIT_API_SECRET")
            if not api_key or not api_secret:
                logger.error("Credenciais da API não encontradas")
                return False

            self.exchange = ccxt.bybit(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "options": {"defaultType": self._mercado},
                }
            )
            self.exchange.load_markets()
            self._pares_usdt = [
                symbol
                for symbol in self.exchange.symbols
                if symbol.endswith("/USDT:USDT")
            ]
            logger.info("Conexão com Bybit inicializada")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar conexao: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Busca klines da Bybit e armazena nos dados fornecidos.

        Args:
            dados: Dicionário pra armazenar os klines
            symbol: Símbolo do par (ex.: "BTCUSDT")
            timeframe: Timeframe (ex.: "1h")
            limit: Número de candles a buscar (padrão: 100)

        Returns:
            bool: True se executado (mesmo com erros tratados), False apenas em falhas críticas
        """
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            limit = kwargs.get("limit", 100)

            if not all([dados, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                return True

            if not isinstance(dados, dict):
                logger.warning(
                    f"Dados devem ser um dicionário para {symbol} - {timeframe}"
                )
                return True

            klines = self.obter_klines(symbol, timeframe, limit)
            if klines:
                dados["crus"] = klines
                logger.debug(f"Klines obtidos para {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar conexao: {e}")
            return True

    def obter_klines(self, symbol: str, timeframe: str, limit: int = 100):
        """
        Obtém klines da Bybit para o símbolo e timeframe especificados.

        Args:
            symbol: Símbolo do par (ex.: "BTCUSDT")
            timeframe: Timeframe (ex.: "1h")
            limit: Número de candles a buscar

        Returns:
            list: Lista de klines ou None se falhar
        """
        try:
            if not self.exchange:
                logger.error("Exchange não inicializada")
                return None
            klines = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return klines if klines else None
        except Exception as e:
            logger.error(f"Erro ao obter klines para {symbol} {timeframe}: {e}")
            return None

    def obter_pares_usdt(self):
        """
        Retorna a lista de pares USDT disponíveis.

        Returns:
            list: Lista de símbolos USDT
        """
        return self._pares_usdt

    def finalizar(self):
        """Finaliza a conexão com a Bybit."""
        try:
            if self.exchange:
                self.exchange.close()
                logger.info("Conexão com Bybit finalizada")
        except Exception as e:
            logger.error(f"Erro ao finalizar conexao: {e}")
