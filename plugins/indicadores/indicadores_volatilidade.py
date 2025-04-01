# indicadores_volatilidade.py
# Plugin para cálculo de indicadores de volatilidade (Bandas de Bollinger, ATR)

from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresVolatilidade(Plugin):
    PLUGIN_NAME = "indicadores_volatilidade"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerentePlugin):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "bb_periodo": 20,
            "bb_desvio_padrao": 2,
            "atr_periodo": 14,
            "volatilidade_periodo": 14,
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

    def calcular_bandas_de_bollinger(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [4])
            close = dados_extraidos[4]
            if len(close) < self.config["bb_periodo"]:
                logger.warning(
                    f"Dados insuficientes para Bandas de Bollinger: {len(close)}/{self.config['bb_periodo']}"
                )
                return np.array([]), np.array([]), np.array([])

            banda_media = talib.SMA(close, timeperiod=self.config["bb_periodo"])
            std_dev = talib.STDDEV(close, timeperiod=self.config["bb_periodo"])
            banda_superior = banda_media + std_dev * self.config["bb_desvio_padrao"]
            banda_inferior = banda_media - std_dev * self.config["bb_desvio_padrao"]
            return banda_superior, banda_media, banda_inferior
        except Exception as e:
            logger.error(f"Erro ao calcular Bandas de Bollinger: {e}")
            return np.array([]), np.array([]), np.array([])

    def calcular_atr(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(high) < self.config["atr_periodo"]:
                logger.warning(
                    f"Dados insuficientes para ATR: {len(high)}/{self.config['atr_periodo']}"
                )
                return np.array([])

            atr = talib.ATR(high, low, close, timeperiod=self.config["atr_periodo"])
            return atr
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return np.array([])

    def calcular_volatilidade(self, dados_completos):
        try:
            if len(dados_completos) < self.config["volatilidade_periodo"]:
                return 0.0
            dados_extraidos = self._extrair_dados(dados_completos, [4])
            close = dados_extraidos[4]
            std = talib.STDDEV(close, timeperiod=self.config["volatilidade_periodo"])
            return (
                min(max(float(std[-1]) / float(close[-1]), 0.0), 1.0)
                if len(std) > 0
                else 0.0
            )
        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {e}")
            return 0.0

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "bandas_bollinger": {"superior": None, "media": None, "inferior": None},
            "atr": None,
            "volatilidade": 0.0,
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["volatilidade"] = resultado_padrao
                return True

            klines = (
                dados_completos.get("crus", [])
                if isinstance(dados_completos, dict)
                else dados_completos
            )
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos["volatilidade"] = resultado_padrao
                return True

            upper, middle, lower = self.calcular_bandas_de_bollinger(klines)
            atr = self.calcular_atr(klines)
            volatilidade = self.calcular_volatilidade(klines)

            resultado = {
                "bandas_bollinger": {
                    "superior": float(upper[-1]) if upper.size > 0 else None,
                    "media": float(middle[-1]) if middle.size > 0 else None,
                    "inferior": float(lower[-1]) if lower.size > 0 else None,
                },
                "atr": float(atr[-1]) if atr.size > 0 else None,
                "volatilidade": volatilidade,
            }

            if isinstance(dados_completos, dict):
                dados_completos["volatilidade"] = resultado
                logger.debug(
                    f"Indicadores de volatilidade calculados para {symbol} - {timeframe}"
                )
            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["volatilidade"] = resultado_padrao
            return True
