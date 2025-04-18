# indicadores_volatilidade.py
# Plugin para cálculo de indicadores de volatilidade (Bandas de Bollinger, ATR)

from plugins.plugin import Plugin
from utils.logging_config import get_logger
import talib
import numpy as np

logger = get_logger(__name__)


class IndicadoresVolatilidade(Plugin):
    PLUGIN_NAME = "indicadores_volatilidade"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicador", "volatilidade"]
    PLUGIN_PRIORIDADE = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = {
            "bb_periodo_base": 20,
            "bb_desvio_padrao": 2,
            "atr_periodo_base": 14,
            "volatilidade_periodo_base": 14,
        }

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

        if len(klines) < 20:
            logger.warning(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}"
            )
            return False

        for item in klines:
            if not isinstance(item, (list, tuple)) or len(item) < 5:
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

    def _ajustar_periodos(self, timeframe: str, volatilidade: float = 0.0) -> dict:
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
            "bb": max(10, int(self.config["bb_periodo_base"] * fator) + ajuste),
            "atr": max(10, int(self.config["atr_periodo_base"] * fator) + ajuste),
            "vol": max(
                10, int(self.config["volatilidade_periodo_base"] * fator) + ajuste
            ),
        }

    def _calcular_volatilidade_base(self, close) -> float:
        """
        Calcula uma estimativa de volatilidade com base no desvio padrão relativo ao preço.

        Args:
            close: Array de preços de fechamento.

        Returns:
            float: Valor da volatilidade ou 0.0 em caso de erro.
        """
        try:
            std = talib.STDDEV(close, timeperiod=10)
            close_final = float(close[-1])
            if close_final == 0:
                return 0.0
            return min(max(float(std[-1]) / close_final, 0.0), 1.0) if std.size else 0.0
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na volatilidade base: {e}")
            return 0.0

    def _extrair_dados(self, dados: list, indices: list) -> dict:
        """
        Extrai arrays NumPy das colunas OHLCV com base nos índices informados.

        Args:
            dados: Lista de k-lines.
            indices: Lista de índices para extração (ex.: [2, 3, 4] para high, low, close).

        Returns:
            dict: Dicionário com arrays NumPy para cada índice.
        """
        try:
            return {
                i: np.array([float(d[i]) for d in dados if len(d) > i]) for i in indices
            }
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao extrair dados de índices {indices}: {e}"
            )
            return {i: np.array([]) for i in indices}

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo dos indicadores de volatilidade e insere o resultado em 'dados_completos["volatilidade"]'.

        Args:
            dados_completos (dict): Dicionário com dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em caso de erro, para não interromper o pipeline).
        """
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
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                if isinstance(dados_completos, dict):
                    dados_completos["volatilidade"] = resultado_padrao
                return True

            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                dados_completos["volatilidade"] = resultado_padrao
                return True

            klines = dados_completos.get("crus", [])
            if not self._validar_klines(klines, symbol, timeframe):
                dados_completos["volatilidade"] = resultado_padrao
                return True

            close = self._extrair_dados(klines, [4])[4]
            if close.size == 0:
                dados_completos["volatilidade"] = resultado_padrao
                return True

            volatilidade_base = self._calcular_volatilidade_base(close)
            periodos = self._ajustar_periodos(timeframe, volatilidade_base)

            # Bollinger Bands
            if len(close) < periodos["bb"]:
                logger.warning(
                    f"[{self.nome}] Menos de {periodos['bb']} candles para Bollinger"
                )
                upper, middle, lower = np.array([]), np.array([]), np.array([])
            else:
                upper, middle, lower = talib.BBANDS(
                    close,
                    timeperiod=periodos["bb"],
                    nbdevup=self.config["bb_desvio_padrao"],
                    nbdevdn=self.config["bb_desvio_padrao"],
                    matype=0,
                )

            # ATR
            dados_ohlc = self._extrair_dados(klines, [2, 3, 4])
            high, low, close_atr = dados_ohlc[2], dados_ohlc[3], dados_ohlc[4]
            atr = talib.ATR(high, low, close_atr, timeperiod=periodos["atr"])
            atr_valor = float(atr[-1]) if atr.size > 0 else None

            resultado = {
                "bandas_bollinger": {
                    "superior": float(upper[-1]) if upper.size else None,
                    "media": float(middle[-1]) if middle.size else None,
                    "inferior": float(lower[-1]) if lower.size else None,
                },
                "atr": atr_valor,
                "volatilidade": round(volatilidade_base, 4),
            }

            dados_completos["volatilidade"] = resultado
            logger.debug(
                f"[{self.nome}] Volatilidade calculada para {symbol} - {timeframe}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos["volatilidade"] = resultado_padrao
            return True
