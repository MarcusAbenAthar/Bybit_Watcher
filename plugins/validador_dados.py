# validador_dados.py

from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class ValidadorDados(Plugin):
    PLUGIN_NAME = "validador_dados"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["validação", "dados"]
    PLUGIN_PRIORIDADE = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_candles = 20

    def inicializar(self, config: dict) -> bool:
        try:
            if not super().inicializar(config):
                return False
            self.min_candles = config.get("validador", {}).get("min_candles", 20)
            logger.info(
                f"ValidadorDados inicializado com min_candles={self.min_candles}"
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar validador_dados: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros obrigatórios ausentes para validação")
                return False

            if not isinstance(dados_completos, dict) or "crus" not in dados_completos:
                logger.warning(f"Formato inválido de dados para {symbol} - {timeframe}")
                return False

            crus = dados_completos["crus"]
            status = "VALIDO" if self._validar(crus, symbol, timeframe) else "INVALIDO"
            dados_completos["validador_dados"] = {"status": status}
            logger.info(f"Dados validados ({status}) para {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar validador_dados: {e}", exc_info=True)
            return False

    def _validar(self, candles, symbol, timeframe) -> bool:
        if not self._validar_symbol(symbol):
            logger.warning(f"Symbol inválido: {symbol}")
            return False
        if not self._validar_timeframe(timeframe):
            logger.warning(f"Timeframe inválido: {timeframe}")
            return False
        if not isinstance(candles, list) or len(candles) < self.min_candles:
            logger.warning(f"Número insuficiente de candles: {len(candles)}")
            return False
        return all(self._validar_candle(c) for c in candles)

    def _validar_symbol(self, symbol: str) -> bool:
        return isinstance(symbol, str) and any(
            symbol.endswith(s) for s in ("USDT", "USD", "BTC")
        )

    def _validar_timeframe(self, tf: str) -> bool:
        timeframes_config = self._config.get("timeframes", [])
        return tf in timeframes_config

    def _validar_candle(self, candle) -> bool:
        try:
            if not isinstance(candle, (list, tuple)) or len(candle) < 6:
                return False
            ts, o, h, l, c, v = map(float, candle[:6])
            return (
                l <= o <= h
                and l <= c <= h
                and v >= 0
                and all(np.isfinite(x) for x in [o, h, l, c, v])
            )
        except Exception as e:
            logger.debug(f"Candle inválido ignorado: {e}")
            return False
