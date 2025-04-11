# Plugin para cálculo de indicadores de tendência (SMA, EMA, MACD, ADX, ATR) de forma adaptativa

from typing import Dict
import numpy as np
import talib
from utils.logging_config import get_logger
from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins

logger = get_logger(__name__)


class IndicadoresTendencia(Plugin):
    PLUGIN_NAME = "indicadores_tendencia"
    PLUGIN_TYPE = "indicador"
    PLUGIN_TAGS = ["indicador", "tendencia"]

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente

    def _ajustar_periodos(self, timeframe: str, volatilidade: float) -> dict:
        multiplicador = 1.0
        if timeframe == "1m":
            multiplicador = 0.5
        elif timeframe == "1d":
            multiplicador = 1.5
        multiplicador += min(max(volatilidade * 2, -0.5), 1.0)

        return {
            "sma_rapida": int(max(5, 9 * multiplicador)),
            "sma_lenta": int(max(10, 21 * multiplicador)),
            "ema_rapida": int(max(5, 12 * multiplicador)),
            "ema_lenta": int(max(10, 26 * multiplicador)),
            "macd_signal": 9,
            "adx_periodo": int(max(5, 14 * multiplicador)),
            "atr_periodo": int(max(5, 14 * multiplicador)),
        }

    def _extrair_ohlcv(self, dados) -> dict:
        try:
            return {
                "high": np.array([float(d[2]) for d in dados]),
                "low": np.array([float(d[3]) for d in dados]),
                "close": np.array([float(d[4]) for d in dados]),
            }
        except Exception as e:
            logger.error(f"Erro ao extrair OHLC: {e}")
            return {"high": np.array([]), "low": np.array([]), "close": np.array([])}

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "medias_moveis": {},
            "macd": {},
            "adx": {},
            "atr": 0.0,
        }

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros obrigatórios ausentes em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["tendencia"] = resultado_padrao
                return True

            candles = dados_completos.get("crus", [])
            if not isinstance(candles, list) or len(candles) < 30:
                logger.warning(f"Candles insuficientes para {symbol} - {timeframe}")
                dados_completos["tendencia"] = resultado_padrao
                return True

            ohlc = self._extrair_ohlcv(candles)
            close = ohlc["close"]
            if len(close) < 30:
                dados_completos["tendencia"] = resultado_padrao
                return True

            volatilidade = np.std(close[-14:]) / np.mean(close[-14:])
            periodos = self._ajustar_periodos(timeframe, volatilidade)

            # Médias móveis
            sma_r = talib.SMA(close, timeperiod=periodos["sma_rapida"])
            sma_l = talib.SMA(close, timeperiod=periodos["sma_lenta"])
            ema_r = talib.EMA(close, timeperiod=periodos["ema_rapida"])
            ema_l = talib.EMA(close, timeperiod=periodos["ema_lenta"])

            # MACD
            macd, signal, hist = talib.MACD(
                close,
                fastperiod=periodos["ema_rapida"],
                slowperiod=periodos["ema_lenta"],
                signalperiod=periodos["macd_signal"],
            )

            # ADX
            adx = talib.ADX(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["adx_periodo"]
            )
            pdi = talib.PLUS_DI(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["adx_periodo"]
            )
            ndi = talib.MINUS_DI(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["adx_periodo"]
            )

            # ATR
            atr = talib.ATR(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["atr_periodo"]
            )

            dados_completos["tendencia"] = {
                "medias_moveis": {
                    "sma_rapida": float(sma_r[-1]) if sma_r.size else None,
                    "sma_lenta": float(sma_l[-1]) if sma_l.size else None,
                    "ema_rapida": float(ema_r[-1]) if ema_r.size else None,
                    "ema_lenta": float(ema_l[-1]) if ema_l.size else None,
                },
                "macd": {
                    "macd": float(macd[-1]) if macd.size else None,
                    "signal": float(signal[-1]) if signal.size else None,
                    "histogram": float(hist[-1]) if hist.size else None,
                },
                "adx": {
                    "adx": float(adx[-1]) if adx.size else None,
                    "pdi": float(pdi[-1]) if pdi.size else None,
                    "ndi": float(ndi[-1]) if ndi.size else None,
                },
                "atr": float(atr[-1]) if atr.size else 0.0,
            }
            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["tendencia"] = resultado_padrao
            return True
