from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
from plugins.plugin import Plugin
import numpy as np
import talib

logger = get_logger(__name__)


class OutrosIndicadores(Plugin):
    PLUGIN_NAME = "outros_indicadores"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicador", "outros", "ichimoku", "fibonacci", "pivots"]
    PLUGIN_PRIORIDADE = 50

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "ichimoku_tenkan_periodo": 9,
            "ichimoku_kijun_periodo": 26,
            "ichimoku_senkou_b_periodo": 52,
        }
        logger.debug(f"{self.nome} inicializado")

    def _calcular_ichimoku(self, high, low):
        try:
            return {
                "tenkan_sen": (
                    talib.MAX(high, timeperiod=self.config["ichimoku_tenkan_periodo"])
                    + talib.MIN(low, timeperiod=self.config["ichimoku_tenkan_periodo"])
                )
                / 2,
                "kijun_sen": (
                    talib.MAX(high, timeperiod=self.config["ichimoku_kijun_periodo"])
                    + talib.MIN(low, timeperiod=self.config["ichimoku_kijun_periodo"])
                )
                / 2,
                "senkou_span_a": None,  # Calculado depois
                "senkou_span_b": (
                    talib.MAX(high, timeperiod=self.config["ichimoku_senkou_b_periodo"])
                    + talib.MIN(
                        low, timeperiod=self.config["ichimoku_senkou_b_periodo"]
                    )
                )
                / 2,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Ichimoku: {e}")
            return {
                k: np.array([])
                for k in ["tenkan_sen", "kijun_sen", "senkou_span_a", "senkou_span_b"]
            }

    def _calcular_fibonacci(self, high, low):
        try:
            maximo, minimo = np.max(high), np.min(low)
            diferenca = maximo - minimo
            return {
                "23.6%": maximo - diferenca * 0.236,
                "38.2%": maximo - diferenca * 0.382,
                "50%": maximo - diferenca * 0.5,
                "61.8%": maximo - diferenca * 0.618,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Fibonacci: {e}")
            return {k: None for k in ["23.6%", "38.2%", "50%", "61.8%"]}

    def _calcular_pivot_points(self, ultimo_candle):
        try:
            h, l, c = (
                float(ultimo_candle[2]),
                float(ultimo_candle[3]),
                float(ultimo_candle[4]),
            )
            pp = (h + l + c) / 3
            return {"PP": pp, "R1": 2 * pp - l, "S1": 2 * pp - h}
        except Exception as e:
            logger.error(f"Erro ao calcular Pivot Points: {e}")
            return {"PP": None, "R1": None, "S1": None}

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "ichimoku": {
                k: None
                for k in ["tenkan_sen", "kijun_sen", "senkou_span_a", "senkou_span_b"]
            },
            "fibonacci": {k: None for k in ["23.6%", "38.2%", "50%", "61.8%"]},
            "pivot_points": {k: None for k in ["PP", "R1", "S1"]},
        }

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros ausentes em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["outros"] = resultado_padrao
                return True

            klines = dados_completos.get("crus", [])
            if not isinstance(klines, list) or len(klines) < 52:
                logger.warning(f"Dados insuficientes para {symbol}-{timeframe}")
                dados_completos["outros"] = resultado_padrao
                return True

            extraidos = self._extrair_dados(klines, [2, 3])
            high, low = extraidos[2], extraidos[3]

            ichimoku = self._calcular_ichimoku(high, low)
            ichimoku["senkou_span_a"] = (
                (ichimoku["tenkan_sen"] + ichimoku["kijun_sen"]) / 2
                if ichimoku["tenkan_sen"].size and ichimoku["kijun_sen"].size
                else np.array([])
            )

            fibonacci = self._calcular_fibonacci(high, low)
            pivot_points = self._calcular_pivot_points(klines[-1])

            resultado = {
                "ichimoku": {
                    k: float(v[-1]) if isinstance(v, np.ndarray) and v.size else None
                    for k, v in ichimoku.items()
                },
                "fibonacci": {
                    k: round(v, 2) if v is not None else None
                    for k, v in fibonacci.items()
                },
                "pivot_points": {
                    k: round(v, 2) if v is not None else None
                    for k, v in pivot_points.items()
                },
            }

            dados_completos["outros"] = resultado
            logger.debug(
                f"Outros indicadores calculados para {symbol}-{timeframe}: {resultado}"
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["outros"] = resultado_padrao
            return True
