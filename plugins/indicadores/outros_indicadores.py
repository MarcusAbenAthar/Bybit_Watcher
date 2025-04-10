# outros_indicadores.py
# Plugin para cálculo de indicadores adicionais (Ichimoku, Fibonacci, Pivot Points)

from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class OutrosIndicadores(Plugin):
    PLUGIN_NAME = "outros_indicadores"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "ichimoku_tenkan_periodo": 9,
            "ichimoku_kijun_periodo": 26,
            "ichimoku_senkou_b_periodo": 52,
        }
        logger.debug(f"{self.nome} inicializado")

    def _calcular_ichimoku(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3])
            high, low = dados_extraidos[2], dados_extraidos[3]
            if len(high) < self.config["ichimoku_senkou_b_periodo"]:
                logger.warning(
                    f"Dados insuficientes para Ichimoku: {len(high)}/{self.config['ichimoku_senkou_b_periodo']}"
                )
                return {
                    "tenkan_sen": np.array([]),
                    "kijun_sen": np.array([]),
                    "senkou_span_a": np.array([]),
                    "senkou_span_b": np.array([]),
                }
            tenkan_sen = (
                talib.MAX(high, timeperiod=self.config["ichimoku_tenkan_periodo"])
                + talib.MIN(low, timeperiod=self.config["ichimoku_tenkan_periodo"])
            ) / 2
            kijun_sen = (
                talib.MAX(high, timeperiod=self.config["ichimoku_kijun_periodo"])
                + talib.MIN(low, timeperiod=self.config["ichimoku_kijun_periodo"])
            ) / 2
            senkou_span_a = (tenkan_sen + kijun_sen) / 2
            senkou_span_b = (
                talib.MAX(high, timeperiod=self.config["ichimoku_senkou_b_periodo"])
                + talib.MIN(low, timeperiod=self.config["ichimoku_senkou_b_periodo"])
            ) / 2
            return {
                "tenkan_sen": tenkan_sen,
                "kijun_sen": kijun_sen,
                "senkou_span_a": senkou_span_a,
                "senkou_span_b": senkou_span_b,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Ichimoku: {e}")
            return {
                "tenkan_sen": np.array([]),
                "kijun_sen": np.array([]),
                "senkou_span_a": np.array([]),
                "senkou_span_b": np.array([]),
            }

    def _calcular_fibonacci(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3])
            high, low = dados_extraidos[2], dados_extraidos[3]
            if not high.size or not low.size:
                return {"23.6%": None, "38.2%": None, "50%": None, "61.8%": None}
            maximo, minimo = float(np.max(high)), float(np.min(low))
            diferenca = maximo - minimo
            return {
                "23.6%": maximo - diferenca * 0.236,
                "38.2%": maximo - diferenca * 0.382,
                "50%": maximo - diferenca * 0.5,
                "61.8%": maximo - diferenca * 0.618,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Fibonacci: {e}")
            return {"23.6%": None, "38.2%": None, "50%": None, "61.8%": None}

    def _calcular_pivot_points(self, dados_completos):
        try:
            if not dados_completos:
                return {"PP": None, "R1": None, "S1": None}
            ultimo = dados_completos[-1]
            h, l, c = float(ultimo[2]), float(ultimo[3]), float(ultimo[4])
            pp = (h + l + c) / 3
            r1 = 2 * pp - l
            s1 = 2 * pp - h
            return {"PP": pp, "R1": r1, "S1": s1}
        except Exception as e:
            logger.error(f"Erro ao calcular Pivot Points: {e}")
            return {"PP": None, "R1": None, "S1": None}

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "ichimoku": {
                "tenkan_sen": None,
                "kijun_sen": None,
                "senkou_span_a": None,
                "senkou_span_b": None,
            },
            "fibonacci": {"23.6%": None, "38.2%": None, "50%": None, "61.8%": None},
            "pivot_points": {"PP": None, "R1": None, "S1": None},
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["outros"] = resultado_padrao
                return True

            klines = (
                dados_completos.get("crus", [])
                if isinstance(dados_completos, dict)
                else dados_completos
            )
            if (
                not isinstance(klines, list) or len(klines) < 52
            ):  # Ichimoku exige 52 períodos
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos["outros"] = resultado_padrao
                return True

            ichimoku = self._calcular_ichimoku(klines)
            fibonacci = self._calcular_fibonacci(klines)
            pivot_points = self._calcular_pivot_points(klines)

            resultado = {
                "ichimoku": {
                    "tenkan_sen": (
                        float(ichimoku["tenkan_sen"][-1])
                        if ichimoku["tenkan_sen"].size
                        else None
                    ),
                    "kijun_sen": (
                        float(ichimoku["kijun_sen"][-1])
                        if ichimoku["kijun_sen"].size
                        else None
                    ),
                    "senkou_span_a": (
                        float(ichimoku["senkou_span_a"][-1])
                        if ichimoku["senkou_span_a"].size
                        else None
                    ),
                    "senkou_span_b": (
                        float(ichimoku["senkou_span_b"][-1])
                        if ichimoku["senkou_span_b"].size
                        else None
                    ),
                },
                "fibonacci": {
                    k: float(v) if v is not None else None for k, v in fibonacci.items()
                },
                "pivot_points": {
                    k: float(v) if v is not None else None
                    for k, v in pivot_points.items()
                },
            }

            if isinstance(dados_completos, dict):
                dados_completos["outros"] = resultado
                logger.debug(
                    f"Indicadores adicionais calculados para {symbol} - {timeframe}"
                )
            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["outros"] = resultado_padrao
            return True
