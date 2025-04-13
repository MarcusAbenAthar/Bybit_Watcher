"""Plugin para conexão com a API da Bybit."""

import os
import ccxt
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Conexao(Plugin):
    """Classe para gerenciar a conexão com a Bybit."""

    PLUGIN_NAME = "conexao"
    PLUGIN_CATEGORIA = "infraestrutura"
    PLUGIN_TAGS = ["conexao", "bybit", "api"]
    PLUGIN_PRIORIDADE = 10

    def __init__(self, gerente=None):
        """Inicializa o plugin de conexão."""
        super().__init__()
        self.exchange = None
        self._mercado = os.getenv("BYBIT_MARKET", "linear")
        self._pares_usdt = []
        self._gerente = gerente
        logger.debug("Instância de Conexao criada.")

    def inicializar(self, config: dict) -> bool:
        """Inicializa a conexão com a Bybit usando credenciais do ambiente."""
        try:
            logger.debug("Inicializando plugin de conexão...")
            if not super().inicializar(config):
                logger.error("Inicialização base falhou.")
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
                s for s in self.exchange.symbols if s.endswith("/USDT:USDT")
            ]
            logger.info("Conexão com Bybit inicializada com sucesso")
            return True
        except Exception as e:
            logger.exception(f"Erro ao inicializar conexao: {e}")
            return False

    def obter_klines(self, symbol: str, timeframe: str, limit: int = 100):
        """Obtém klines da Bybit para o símbolo e timeframe especificados."""
        try:
            logger.debug(
                f"Entrando em obter_klines com symbol={symbol}, timeframe={timeframe}, limit={limit}"
            )
            if not self.exchange:
                logger.error("Exchange não inicializada")
                return None

            klines = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.debug(
                f"Raw klines recebidos ({len(klines)}): {klines[:2]}..."
            )  # Só os 2 primeiros para não poluir

            if isinstance(klines, list) and klines:
                logger.debug("Klines válidos retornados.")
                return klines
            else:
                logger.warning(f"Klines vazios ou inválidos para {symbol} {timeframe}")
                return None
        except Exception as e:
            logger.exception(f"Erro ao obter klines para {symbol} {timeframe}: {e}")
            return None

    def executar(self, *args, **kwargs) -> bool:
        logger.debug("Iniciando execução do plugin Conexao.")
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            limit = kwargs.get("limit", 100)

            logger.debug(
                f"Parâmetros recebidos: symbol={symbol}, timeframe={timeframe}, limit={limit}"
            )

            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros obrigatórios ausentes.")
                return True

            if not isinstance(dados_completos, dict):
                logger.warning(
                    f"dados_completos deve ser dict, recebido: {type(dados_completos)}"
                )
                return True

            # Ajuste dinâmico de limit
            if timeframe in ["1m", "5m", "15m"]:
                limit = 200
            elif timeframe in ["1h", "4h"]:
                limit = 100
            else:
                limit = 50
            logger.debug(f"Limit ajustado para {limit}")

            klines = self.obter_klines(symbol, timeframe, limit)

            if klines:
                logger.debug(
                    f"Recebido {len(klines)} candles para {symbol} - {timeframe}"
                )
                for i, kline in enumerate(klines[:3]):  # Limita os logs
                    ts, open_, high, low, close, vol = kline
                    logger.debug(
                        f"Candle {i + 1}: Timestamp={ts}, Open={open_}, High={high}, "
                        f"Low={low}, Close={close}, Volume={vol}"
                    )
                dados_completos["crus"] = klines
                logger.debug(f"Klines adicionados a dados_completos['crus']")
            else:
                logger.warning(f"Nenhum kline recebido para {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.exception(f"Erro ao executar conexao: {e}")
            return True

    def obter_pares_usdt(self):
        """Retorna a lista de pares USDT disponíveis."""
        logger.debug("Listando pares USDT disponíveis.")
        return self._pares_usdt

    def finalizar(self):
        """Finaliza a conexão com a Bybit."""
        try:
            if self.exchange:
                self.exchange.close()
                logger.info("Conexão com Bybit finalizada")
            else:
                logger.debug("Exchange não estava ativa ao finalizar.")
        except Exception as e:
            logger.exception(f"Erro ao finalizar conexao: {e}")
