# outros_indicadores.py
"""Plugin para calcular indicadores adicionais como Ichimoku, Fibonacci e Pivot Points."""

from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class OutrosIndicadores(Plugin):
    """Plugin para indicadores adicionais."""

    PLUGIN_NAME = "outros_indicadores"
    PLUGIN_TYPE = "indicador"

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo de indicadores adicionais e gera sinal.

        Args:
            dados: Lista de candles [timestamp, open, high, low, close, volume]
            symbol: Símbolo do par (ex.: "XRPUSDT")
            timeframe: Timeframe analisado (ex.: "1h")

        Returns:
            bool: True se executado com sucesso, mesmo com erros tratados
        """
        resultado_padrao = {
            "outros_indicadores": {
                "ichimoku": {
                    "tenkan_sen": None,
                    "kijun_sen": None,
                    "senkou_span_a": None,
                    "senkou_span_b": None,
                },
                "fibonacci": {"23.6%": None, "38.2%": None, "50%": None, "61.8%": None},
                "pivot_points": {"PP": None, "R1": None, "S1": None},
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
            }
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            if (
                not isinstance(dados, list) or len(dados) < 52
            ):  # Ichimoku exige 52 períodos
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            indicadores = self._calcular_indicadores(dados)
            sinal = self._gerar_sinal(dados)
            indicadores.update(sinal)

            if isinstance(dados, dict):
                dados["outros_indicadores"] = indicadores
            logger.debug(f"Indicadores calculados para {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar outros_indicadores: {e}")
            if isinstance(dados, dict):
                dados.update(resultado_padrao)
            return True

    def _calcular_indicadores(self, dados):
        """Calcula Ichimoku, Fibonacci e Pivot Points."""
        ichimoku = self._calcular_ichimoku(dados)
        fibonacci = self._calcular_fibonacci(dados)
        pivot_points = self._calcular_pivot_points(dados)
        return {
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
                k: float(v) if v is not None else None for k, v in pivot_points.items()
            },
        }

    def _calcular_ichimoku(self, dados):
        """Calcula componentes do Ichimoku Cloud."""
        try:
            high = np.array([float(candle[2]) for candle in dados], dtype=np.float64)
            low = np.array([float(candle[3]) for candle in dados], dtype=np.float64)
            if len(high) < 52:
                return {
                    "tenkan_sen": np.array([]),
                    "kijun_sen": np.array([]),
                    "senkou_span_a": np.array([]),
                    "senkou_span_b": np.array([]),
                }
            tenkan_sen = (
                talib.MAX(high, timeperiod=9) + talib.MIN(low, timeperiod=9)
            ) / 2
            kijun_sen = (
                talib.MAX(high, timeperiod=26) + talib.MIN(low, timeperiod=26)
            ) / 2
            senkou_span_a = (tenkan_sen + kijun_sen) / 2
            senkou_span_b = (
                talib.MAX(high, timeperiod=52) + talib.MIN(low, timeperiod=52)
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

    def _calcular_fibonacci(self, dados):
        """Calcula níveis de Fibonacci Retracement."""
        try:
            high = np.array([float(candle[2]) for candle in dados], dtype=np.float64)
            low = np.array([float(candle[3]) for candle in dados], dtype=np.float64)
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

    def _calcular_pivot_points(self, dados):
        """Calcula Pivot Points do último candle."""
        try:
            if not dados:
                return {"PP": None, "R1": None, "S1": None}
            ultimo = dados[-1]
            h, l, c = float(ultimo[2]), float(ultimo[3]), float(ultimo[4])
            pp = (h + l + c) / 3
            r1 = 2 * pp - l
            s1 = 2 * pp - h
            return {"PP": pp, "R1": r1, "S1": s1}
        except Exception as e:
            logger.error(f"Erro ao calcular Pivot Points: {e}")
            return {"PP": None, "R1": None, "S1": None}

    def _gerar_sinal(self, dados):
        """Gera sinal baseado nos indicadores calculados."""
        try:
            ultimo_preco = float(dados[-1][4])
            ichimoku = self._calcular_ichimoku(dados)
            fibonacci = self._calcular_fibonacci(dados)
            pivot_points = self._calcular_pivot_points(dados)

            confirmacoes_alta = 0
            confirmacoes_baixa = 0
            total = 0

            if ichimoku["tenkan_sen"].size:
                total += 1
                if (
                    ichimoku["tenkan_sen"][-1] > ichimoku["kijun_sen"][-1]
                    and ultimo_preco > ichimoku["senkou_span_a"][-1]
                ):
                    confirmacoes_alta += 1
                elif (
                    ichimoku["tenkan_sen"][-1] < ichimoku["kijun_sen"][-1]
                    and ultimo_preco < ichimoku["senkou_span_a"][-1]
                ):
                    confirmacoes_baixa += 1

            if fibonacci["50%"] is not None:
                total += 1
                if (
                    ultimo_preco > fibonacci["50%"]
                    and ultimo_preco <= fibonacci["61.8%"]
                ):
                    confirmacoes_alta += 1
                elif (
                    ultimo_preco < fibonacci["38.2%"]
                    and ultimo_preco >= fibonacci["23.6%"]
                ):
                    confirmacoes_baixa += 1

            if pivot_points["PP"] is not None:
                total += 1
                if (
                    ultimo_preco > pivot_points["PP"]
                    and ultimo_preco <= pivot_points["R1"]
                ):
                    confirmacoes_alta += 1
                elif (
                    ultimo_preco < pivot_points["PP"]
                    and ultimo_preco >= pivot_points["S1"]
                ):
                    confirmacoes_baixa += 1

            confianca = (
                max(confirmacoes_alta, confirmacoes_baixa) / total * 100
                if total > 0
                else 0.0
            )
            direcao = (
                "ALTA"
                if confirmacoes_alta > confirmacoes_baixa
                else "BAIXA" if confirmacoes_baixa > confirmacoes_alta else "NEUTRO"
            )
            forca = (
                "FORTE" if confianca >= 80 else "MÉDIA" if confianca >= 50 else "FRACA"
            )
            return {"direcao": direcao, "forca": forca, "confianca": confianca}
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
