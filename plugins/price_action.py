# price_action.py
from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class PriceAction(Plugin):
    PLUGIN_NAME = "price_action"
    PLUGIN_TYPE = "essencial"

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "price_action": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "padrao": None,
            }
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            if not isinstance(dados, list) or len(dados) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            sinal = self.gerar_sinal(dados)
            if isinstance(dados, dict):
                dados["price_action"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar price_action: {e}")
            if isinstance(dados, dict):
                dados.update(resultado_padrao)
            return True

    def gerar_sinal(self, dados):
        try:
            dados_extraidos = self._extrair_dados(dados, [1, 2, 3, 4])
            open_prices, high, low, close = (
                dados_extraidos[1],
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(close) < 20:
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "padrao": None,
                }

            ultimo_candle = {
                "open": open_prices[-1],
                "high": high[-1],
                "low": low[-1],
                "close": close[-1],
            }
            padrao = self._identificar_padrao(ultimo_candle)
            forca = self._calcular_forca(ultimo_candle)
            tendencia = self._analisar_tendencia(ultimo_candle)

            confianca = min(forca * 100, 100.0) if padrao != "indefinido" else 0.0
            direcao = tendencia if tendencia != "LATERAL" else "NEUTRO"
            forca_str = "FORTE" if forca > 0.7 else "MÉDIA" if forca > 0.3 else "FRACA"

            return {
                "direcao": direcao,
                "forca": forca_str,
                "confianca": confianca,
                "padrao": padrao,
            }
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "padrao": None,
            }

    def _identificar_padrao(self, candle):
        try:
            amplitude = candle["high"] - candle["low"]
            corpo = abs(candle["close"] - candle["open"])
            if not amplitude:
                return "indefinido"
            return (
                "doji"
                if corpo / amplitude < 0.1
                else "alta" if candle["close"] > candle["open"] else "baixa"
            )
        except Exception as e:
            logger.error(f"Erro ao identificar padrão: {e}")
            return "indefinido"

    def _calcular_forca(self, candle):
        try:
            amplitude = candle["high"] - candle["low"]
            corpo = abs(candle["close"] - candle["open"])
            return corpo / amplitude if amplitude > 0 else 0.0
        except Exception as e:
            logger.error(f"Erro ao calcular força: {e}")
            return 0.0

    def _analisar_tendencia(self, candle):
        try:
            return (
                "ALTA"
                if candle["close"] > candle["open"]
                else "BAIXA" if candle["close"] < candle["open"] else "LATERAL"
            )
        except Exception as e:
            logger.error(f"Erro ao analisar tendência: {e}")
            return "LATERAL"
