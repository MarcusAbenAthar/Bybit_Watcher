# validador_dados.py
from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class ValidadorDados(Plugin):
    PLUGIN_NAME = "validador_dados"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self.min_candles = 20

    def inicializar(self, config: dict) -> bool:
        try:
            if not super().inicializar(config):
                return False
            self.min_candles = config.get("validador", {}).get("min_candles", 20)
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar validador_dados: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        try:
            dados_completos = kwargs.get(
                "dados_completos"
            )  # Ajustado pra dados_completos
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                return True

            if not isinstance(dados_completos, dict) or "crus" not in dados_completos:
                logger.warning(
                    f"Dados devem ser um dicionário com 'crus' para {symbol} - {timeframe}"
                )
                return True

            dados_crus = dados_completos["crus"]
            if not isinstance(dados_crus, list):
                logger.warning(f"'crus' deve ser uma lista para {symbol} - {timeframe}")
                return True

            if self._validar_dados(dados_crus, symbol, timeframe):
                logger.info(f"Dados validados para {symbol} ({timeframe})")
                dados_completos["validador_dados"] = {"status": "VALIDO"}
                return True
            else:
                dados_completos["validador_dados"] = {"status": "INVALIDO"}
                return True
        except Exception as e:
            logger.error(f"Erro ao executar validador_dados: {e}")
            return True

    def _validar_dados(self, dados_completos, symbol, timeframe):
        if not self._validar_symbol(symbol) or not self._validar_timeframe(timeframe):
            return False
        if len(dados_completos) < self.min_candles:
            logger.error(f"Quantidade insuficiente de candles: {len(dados_completos)}")
            return False
        return all(self._validar_candle(candle) for candle in dados_completos)

    def _validar_symbol(self, symbol):
        return isinstance(symbol, str) and symbol.endswith(("USDT", "USD", "BTC"))

    def _validar_timeframe(self, timeframe):
        validos = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
        return timeframe in validos

    def _validar_candle(self, candle):
        try:
            if not isinstance(candle, (list, tuple)) or len(candle) < 6:
                return False
            timestamp, o, h, l, c, v = map(float, candle[:6])
            return (
                l <= o <= h
                and l <= c <= h
                and v >= 0
                and not any(np.isnan(x) or np.isinf(x) for x in [o, h, l, c, v])
            )
        except Exception as e:
            logger.error(f"Erro ao validar candle: {e}")
            return False
