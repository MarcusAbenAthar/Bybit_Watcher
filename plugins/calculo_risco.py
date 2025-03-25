# calculo_risco.py
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class CalculoRisco(Plugin):
    PLUGIN_NAME = "calculo_risco"
    PLUGIN_TYPE = "essencial"

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "calculo_risco": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {},
            }
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            if not isinstance(dados_completos, list) or len(dados_completos) < 50:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            sinal = self.gerar_sinal(dados_completos)
            if isinstance(dados_completos, dict):
                dados_completos["calculo_risco"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar calculo_risco: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def gerar_sinal(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(close) < 50:
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "indicadores": {},
                }

            sinal = {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {
                    "tendencia": self._confirmar_tendencia(close),
                    "volatilidade": self._verificar_volatilidade(high, low, close),
                    "momentum": self._calcular_momentum(close),
                    "volume": self._verificar_volume(volume),
                },
            }

            if sinal["indicadores"]["tendencia"]:
                sinal["confianca"] += 0.4
            if abs(sinal["indicadores"]["momentum"]) > 0.6:
                sinal["confianca"] += 0.3
            if sinal["indicadores"]["volatilidade"] < 0.5:
                sinal["confianca"] += 0.3
            if sinal["indicadores"]["volume"]:
                sinal["confianca"] += 0.2

            sinal["confianca"] = min(sinal["confianca"], 1.0)
            sinal["forca"] = (
                "FORTE"
                if sinal["confianca"] >= 0.8
                else "MÉDIA" if sinal["confianca"] >= 0.6 else "FRACA"
            )
            momentum = sinal["indicadores"]["momentum"]
            sinal["direcao"] = (
                "ALTA" if momentum > 0.2 else "BAIXA" if momentum < -0.2 else "NEUTRO"
            )

            return sinal
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {},
            }

    def _confirmar_tendencia(self, close):
        try:
            ma_curta = talib.SMA(close, timeperiod=9)
            ma_media = talib.SMA(close, timeperiod=21)
            ma_longa = talib.SMA(close, timeperiod=50)
            macd, signal, _ = talib.MACD(close)
            tendencia_mas = (
                ma_curta[-1] > ma_media[-1] > ma_longa[-1]
                or ma_curta[-1] < ma_media[-1] < ma_longa[-1]
            )
            tendencia_macd = macd[-1] > signal[-1] or macd[-1] < signal[-1]
            return tendencia_mas and tendencia_macd
        except Exception as e:
            logger.error(f"Erro ao confirmar tendência: {e}")
            return False

    def _verificar_volatilidade(self, high, low, close):
        try:
            atr = talib.ATR(high, low, close, timeperiod=14)
            return float(atr[-1]) / float(close[-1]) if atr.size else 1.0
        except Exception as e:
            logger.error(f"Erro ao verificar volatilidade: {e}")
            return 1.0

    def _calcular_momentum(self, close):
        try:
            rsi = talib.RSI(close, timeperiod=14)
            return (rsi[-1] - 50) / 50 if rsi.size else 0.0
        except Exception as e:
            logger.error(f"Erro ao calcular momentum: {e}")
            return 0.0

    def _verificar_volume(self, volume):
        try:
            return np.mean(volume[-20:]) >= 1000
        except Exception as e:
            logger.error(f"Erro ao verificar volume: {e}")
            return False
