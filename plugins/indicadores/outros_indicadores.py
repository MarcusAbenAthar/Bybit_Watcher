from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
from plugins.plugin import Plugin
import numpy as np
import talib

logger = get_logger(__name__)


class OutrosIndicadores(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin OutrosIndicadores, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.debug("OutrosIndicadores finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar OutrosIndicadores: {e}")

    """
    Plugin para outros indicadores customizados.
    - Responsabilidade única: cálculo de indicadores customizados.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "outros_indicadores"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicadores", "custom", "analise"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin OutrosIndicadores.
        """
        return []

    PLUGIN_NAME = "outros_indicadores"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicador", "outros", "ichimoku", "fibonacci", "pivots"]
    PLUGIN_PRIORIDADE = 50

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "ichimoku_tenkan_periodo_base": 9,
            "ichimoku_kijun_periodo_base": 26,
            "ichimoku_senkou_b_periodo_base": 52,
            "ichimoku_shift": 26,  # Período de deslocamento para Senkou Span e Chikou Span
            "fibonacci_janela_base": 20,  # Janela para cálculo de Fibonacci
        }
        logger.debug(f"[{self.nome}] inicializado")

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    def _validar_klines(self, klines, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de klines.

        Args:
            klines: Lista de k-lines.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(klines, list):
            logger.error(f"[{self.nome}] klines não é uma lista: {type(klines)}")
            return False

        if len(klines) < 52:
            logger.warning(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}"
            )
            return False

        for item in klines:
            if not isinstance(item, (list, tuple)) or len(item) < 6:
                logger.error(
                    f"[{self.nome}] Item inválido em klines para {symbol} - {timeframe}: {item}"
                )
                return False
            for idx in [2, 3, 4]:  # high, low, close
                if not isinstance(item[idx], (int, float)):
                    try:
                        float(item[idx])
                    except (TypeError, ValueError):
                        logger.error(
                            f"[{self.nome}] Valor não numérico em klines[{idx}]: {item[idx]}"
                        )
                        return False

        return True

    def _calcular_volatilidade(self, close, periodo=14) -> float:
        """
        Calcula a volatilidade com base no desvio padrão relativo.

        Args:
            close: Array de preços de fechamento.
            periodo: Período para cálculo.

        Returns:
            float: Valor da volatilidade ou 0.0 em caso de erro.
        """
        try:
            std = talib.STDDEV(close, timeperiod=periodo)
            return (
                float(std[-1]) / float(close[-1])
                if std.size > 0 and close[-1] != 0
                else 0.0
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular volatilidade: {e}")
            return 0.0

    def _ajustar_periodos(self, timeframe: str, volatilidade: float) -> dict:
        """
        Ajusta dinamicamente os períodos dos indicadores com base no timeframe e volatilidade.

        Args:
            timeframe (str): Timeframe (ex.: '1m', '1d').
            volatilidade (float): Volatilidade calculada.

        Returns:
            dict: Períodos ajustados para indicadores.
        """
        ajuste = int(volatilidade * 10)
        if timeframe == "1m":
            fator = 0.5
        elif timeframe == "1d":
            fator = 1.5
        else:
            fator = 1.0

        return {
            "ichimoku_tenkan": max(
                5, int(self.config["ichimoku_tenkan_periodo_base"] * fator) + ajuste
            ),
            "ichimoku_kijun": max(
                10, int(self.config["ichimoku_kijun_periodo_base"] * fator) + ajuste
            ),
            "ichimoku_senkou_b": max(
                20, int(self.config["ichimoku_senkou_b_periodo_base"] * fator) + ajuste
            ),
            "fibonacci_janela": max(
                10, int(self.config["fibonacci_janela_base"] * fator) + ajuste
            ),
        }

    def _calcular_ichimoku(self, high, low, close):
        """
        Calcula os componentes do Ichimoku Cloud.

        Args:
            high, low, close: Arrays de preços high, low e close.

        Returns:
            dict: Componentes do Ichimoku (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span).
        """
        try:
            periodos = self.config["periodos"]
            tenkan_sen = (
                talib.MAX(high, timeperiod=periodos["ichimoku_tenkan"])
                + talib.MIN(low, timeperiod=periodos["ichimoku_tenkan"])
            ) / 2
            kijun_sen = (
                talib.MAX(high, timeperiod=periodos["ichimoku_kijun"])
                + talib.MIN(low, timeperiod=periodos["ichimoku_kijun"])
            ) / 2
            senkou_span_b = (
                talib.MAX(high, timeperiod=periodos["ichimoku_senkou_b"])
                + talib.MIN(low, timeperiod=periodos["ichimoku_senkou_b"])
            ) / 2
            # Calcular Senkou Span A como (tenkan_sen + kijun_sen) / 2, deslocado à frente
            senkou_span_a = (tenkan_sen + kijun_sen) / 2
            if senkou_span_a.size:
                senkou_span_a = np.roll(senkou_span_a, self.config["ichimoku_shift"])
                senkou_span_a[: self.config["ichimoku_shift"]] = np.nan
            # Calcular Chikou Span como close deslocado para trás
            chikou_span = close.copy()
            if chikou_span.size:
                chikou_span = np.roll(chikou_span, -self.config["ichimoku_shift"])
                chikou_span[-self.config["ichimoku_shift"] :] = np.nan

            return {
                "tenkan_sen": tenkan_sen,
                "kijun_sen": kijun_sen,
                "senkou_span_a": senkou_span_a,
                "senkou_span_b": senkou_span_b,
                "chikou_span": chikou_span,
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular Ichimoku: {e}")
            return {
                k: np.array([])
                for k in [
                    "tenkan_sen",
                    "kijun_sen",
                    "senkou_span_a",
                    "senkou_span_b",
                    "chikou_span",
                ]
            }

    def _calcular_fibonacci(self, high, low, janela):
        """
        Calcula níveis de Fibonacci com base nos preços máximo e mínimo em uma janela.

        Args:
            high, low: Arrays de preços high e low.
            janela: Número de períodos para considerar.

        Returns:
            dict: Níveis de Fibonacci (23.6%, 38.2%, 50%, 61.8%).
        """
        try:
            if high.size < janela or low.size < janela:
                logger.warning(
                    f"[{self.nome}] Dados insuficientes para Fibonacci (janela={janela})"
                )
                return {k: None for k in ["23.6%", "38.2%", "50%", "61.8%"]}
            high_janela = high[-janela:]
            low_janela = low[-janela:]
            maximo, minimo = np.max(high_janela), np.min(low_janela)
            diferenca = maximo - minimo
            return {
                "23.6%": maximo - diferenca * 0.236,
                "38.2%": maximo - diferenca * 0.382,
                "50%": maximo - diferenca * 0.5,
                "61.8%": maximo - diferenca * 0.618,
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular Fibonacci: {e}")
            return {k: None for k in ["23.6%", "38.2%", "50%", "61.8%"]}

    def _calcular_pivot_points(self, ultimo_candle):
        """
        Calcula Pivot Points com base no último candle.

        Args:
            ultimo_candle: Último candle [timestamp, open, high, low, close, volume].

        Returns:
            dict: Pivot Point (PP), Resistência 1 (R1), Suporte 1 (S1).
        """
        try:
            h, l, c = (
                float(ultimo_candle[2]),
                float(ultimo_candle[3]),
                float(ultimo_candle[4]),
            )
            pp = (h + l + c) / 3
            return {"PP": pp, "R1": 2 * pp - l, "S1": 2 * pp - h}
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular Pivot Points: {e}")
            return {"PP": None, "R1": None, "S1": None}

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo dos indicadores e armazena resultados.

        Args:
            dados_completos (dict): Dicionário com dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em caso de erro, para não interromper o pipeline).
        """
        resultado_padrao = {
            "ichimoku": {
                k: None
                for k in [
                    "tenkan_sen",
                    "kijun_sen",
                    "senkou_span_a",
                    "senkou_span_b",
                    "chikou_span",
                ]
            },
            "fibonacci": {k: None for k in ["23.6%", "38.2%", "50%", "61.8%"]},
            "pivot_points": {k: None for k in ["PP", "R1", "S1"]},
        }

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros ausentes")
                if isinstance(dados_completos, dict):
                    dados_completos["outros"] = resultado_padrao
                return True

            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                dados_completos["outros"] = resultado_padrao
                return True

            klines = dados_completos.get("crus", [])
            if not self._validar_klines(klines, symbol, timeframe):
                dados_completos["outros"] = resultado_padrao
                return True

            extraidos = self._extrair_dados(klines, [2, 3, 4])  # high, low, close
            high, low, close = extraidos[2], extraidos[3], extraidos[4]
            if not all([high.size >= 52, low.size >= 52, close.size >= 52]):
                logger.warning(
                    f"[{self.nome}] Dados extraídos insuficientes para {symbol} - {timeframe}"
                )
                dados_completos["outros"] = resultado_padrao
                return True

            volatilidade = self._calcular_volatilidade(close)
            self.config["periodos"] = self._ajustar_periodos(timeframe, volatilidade)

            ichimoku = self._calcular_ichimoku(high, low, close)
            fibonacci = self._calcular_fibonacci(
                high, low, self.config["periodos"]["fibonacci_janela"]
            )
            pivot_points = self._calcular_pivot_points(klines[-1])

            resultado = {
                "ichimoku": {
                    k: (
                        float(v[-1])
                        if isinstance(v, np.ndarray) and v.size and not np.isnan(v[-1])
                        else None
                    )
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
                f"[{self.nome}] Outros indicadores calculados para {symbol} - {timeframe}: {resultado}"
            )
            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["outros"] = resultado_padrao
            return True
