# indicadores_tendencia.py
# Plugin para cálculo de indicadores de tendência (SMA, EMA, MACD, ADX, ATR)

from typing import Dict
import numpy as np
import talib
from utils.logging_config import get_logger
from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin

logger = get_logger(__name__)


class IndicadoresTendencia(Plugin):
    PLUGIN_NAME = "indicadores_tendencia"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerentePlugin):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "sma_rapida": 9,
            "sma_lenta": 21,
            "ema_rapida": 12,
            "ema_lenta": 26,
            "macd_signal": 9,
            "adx_periodo": 14,
            "atr_periodo": 14,
        }

    def _extrair_dados(self, dados_completos, indices):
        try:
            valores = {idx: [] for idx in indices}
            for candle in dados_completos:
                if any(
                    candle[i] is None or str(candle[i]).strip() == "" for i in indices
                ):
                    continue
                try:
                    for idx in indices:
                        valor = float(
                            str(candle[idx]).replace("e", "").replace("E", "")
                        )
                        valores[idx].append(valor)
                except (ValueError, TypeError):
                    continue
            if not all(valores.values()):
                logger.warning(f"Dados insuficientes ou inválidos em {self.nome}")
                return {idx: np.array([]) for idx in indices}
            return {idx: np.array(valores[idx], dtype=np.float64) for idx in indices}
        except Exception as e:
            logger.error(f"Erro ao extrair dados em {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}

    def calcular_medias_moveis(self, dados_completos) -> Dict[str, float]:
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [4])
            close = dados_extraidos[4]
            if len(close) < max(self.config["sma_lenta"], self.config["ema_lenta"]):
                return {
                    "sma_rapida": None,
                    "sma_lenta": None,
                    "ema_rapida": None,
                    "ema_lenta": None,
                }

            sma_rapida = talib.SMA(close, timeperiod=self.config["sma_rapida"])
            sma_lenta = talib.SMA(close, timeperiod=self.config["sma_lenta"])
            ema_rapida = talib.EMA(close, timeperiod=self.config["ema_rapida"])
            ema_lenta = talib.EMA(close, timeperiod=self.config["ema_lenta"])

            return {
                "sma_rapida": float(sma_rapida[-1]) if sma_rapida.size else None,
                "sma_lenta": float(sma_lenta[-1]) if sma_lenta.size else None,
                "ema_rapida": float(ema_rapida[-1]) if ema_rapida.size else None,
                "ema_lenta": float(ema_lenta[-1]) if ema_lenta.size else None,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular médias móveis: {e}")
            return {
                "sma_rapida": None,
                "sma_lenta": None,
                "ema_rapida": None,
                "ema_lenta": None,
            }

    def calcular_macd(self, dados_completos) -> Dict[str, float]:
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [4])
            close = dados_extraidos[4]
            if len(close) < self.config["ema_lenta"]:
                return {"macd": None, "signal": None, "histogram": None}

            macd_line, signal_line, histogram = talib.MACD(
                close,
                fastperiod=self.config["ema_rapida"],
                slowperiod=self.config["ema_lenta"],
                signalperiod=self.config["macd_signal"],
            )
            return {
                "macd": float(macd_line[-1]) if macd_line.size else None,
                "signal": float(signal_line[-1]) if signal_line.size else None,
                "histogram": float(histogram[-1]) if histogram.size else None,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular MACD: {e}")
            return {"macd": None, "signal": None, "histogram": None}

    def calcular_adx(self, dados_completos) -> Dict[str, float]:
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(high) < self.config["adx_periodo"]:
                return {"adx": None, "pdi": None, "ndi": None}

            adx = talib.ADX(high, low, close, timeperiod=self.config["adx_periodo"])
            pdi = talib.PLUS_DI(high, low, close, timeperiod=self.config["adx_periodo"])
            ndi = talib.MINUS_DI(
                high, low, close, timeperiod=self.config["adx_periodo"]
            )

            return {
                "adx": float(adx[-1]) if adx.size else None,
                "pdi": float(pdi[-1]) if pdi.size else None,
                "ndi": float(ndi[-1]) if ndi.size else None,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular ADX: {e}")
            return {"adx": None, "pdi": None, "ndi": None}

    def calcular_atr(self, dados_completos) -> float:
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(high) < self.config["atr_periodo"]:
                return 0.0

            atr = talib.ATR(high, low, close, timeperiod=self.config["atr_periodo"])
            return float(atr[-1]) if atr.size else 0.0
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return 0.0

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "medias_moveis": {
                "sma_rapida": None,
                "sma_lenta": None,
                "ema_rapida": None,
                "ema_lenta": None,
            },
            "macd": {"macd": None, "signal": None, "histogram": None},
            "adx": {"adx": None, "pdi": None, "ndi": None},
            "atr": 0.0,
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["tendencia"] = resultado_padrao
                return True

            klines = (
                dados_completos.get("crus", [])
                if isinstance(dados_completos, dict)
                else dados_completos
            )
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos["tendencia"] = resultado_padrao
                return True

            medias = self.calcular_medias_moveis(klines)
            macd = self.calcular_macd(klines)
            adx = self.calcular_adx(klines)
            atr = self.calcular_atr(klines)

            resultado = {
                "medias_moveis": medias,
                "macd": macd,
                "adx": adx,
                "atr": atr,
            }

            if isinstance(dados_completos, dict):
                dados_completos["tendencia"] = resultado
                logger.debug(
                    f"Indicadores de tendência calculados para {symbol} - {timeframe}"
                )

            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["tendencia"] = resultado_padrao
            return True
