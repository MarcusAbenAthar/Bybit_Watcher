# indicadores_osciladores.py
# Plugin para cálculo de indicadores osciladores (RSI, Estocástico, MFI)

from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresOsciladores(Plugin):
    PLUGIN_NAME = "indicadores_osciladores"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente

    def calcular_rsi(self, dados_completos, symbol, timeframe, periodo=14):
        try:
            if timeframe == "1m":
                periodo = max(7, periodo // 2)
            elif timeframe == "1d":
                periodo = min(28, periodo * 2)
            volatilidade = self.calcular_volatilidade(dados_completos)
            periodo = max(7, min(28, periodo + int(volatilidade * 10)))

            dados_extraidos = self._extrair_dados(dados_completos, [4])
            close = dados_extraidos[4]
            if len(close) < periodo:
                return np.array([])

            rsi = talib.RSI(close, timeperiod=periodo)
            logger.debug(f"RSI calculado para {symbol} - {timeframe}")
            return rsi
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {e}")
            return np.array([])

    def calcular_estocastico(
        self, dados_completos, timeframe, fastk_period=5, slowk_period=3, slowd_period=3
    ):
        try:
            if timeframe == "1m":
                fastk_period = max(3, fastk_period // 2)
                slowk_period = max(2, slowk_period // 2)
                slowd_period = max(2, slowd_period // 2)
            elif timeframe == "1d":
                fastk_period = min(10, fastk_period * 2)
                slowk_period = min(6, slowk_period * 2)
                slowd_period = min(6, slowd_period * 2)
            volatilidade = self.calcular_volatilidade(dados_completos)
            ajuste = int(volatilidade * 3)
            fastk_period = max(3, min(10, fastk_period + ajuste))
            slowk_period = max(2, min(6, slowk_period + ajuste))
            slowd_period = max(2, min(6, slowd_period + ajuste))

            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(high) < max(fastk_period, slowk_period, slowd_period):
                return np.array([]), np.array([])

            slowk, slowd = talib.STOCH(
                high,
                low,
                close,
                fastk_period=fastk_period,
                slowk_period=slowk_period,
                slowk_matype=0,
                slowd_period=slowd_period,
                slowd_matype=0,
            )
            return slowk, slowd
        except Exception as e:
            logger.error(f"Erro ao calcular Estocástico: {e}")
            return np.array([]), np.array([])

    def calcular_mfi(self, dados_completos, periodo=14):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(high) < periodo:
                return np.array([])

            mfi = talib.MFI(high, low, close, volume, timeperiod=periodo)
            return mfi
        except Exception as e:
            logger.error(f"Erro ao calcular MFI: {e}")
            return np.array([])

    def calcular_volatilidade(self, dados_completos, periodo=14):
        try:
            if len(dados_completos) < periodo:
                return 0.0
            dados_extraidos = self._extrair_dados(dados_completos, [4])
            close = dados_extraidos[4]
            std = talib.STDDEV(close, timeperiod=periodo)
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
            "rsi": None,
            "estocastico": {"slowk": None, "slowd": None},
            "mfi": None,
            "volatilidade": 0.0,
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["osciladores"] = resultado_padrao
                return True

            klines = (
                dados_completos.get("crus", [])
                if isinstance(dados_completos, dict)
                else dados_completos
            )
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos["osciladores"] = resultado_padrao
                return True

            rsi = self.calcular_rsi(klines, symbol, timeframe)
            slowk, slowd = self.calcular_estocastico(klines, timeframe)
            mfi = self.calcular_mfi(klines)
            volatilidade = self.calcular_volatilidade(klines)

            resultado = {
                "rsi": float(rsi[-1]) if rsi.size > 0 else None,
                "estocastico": {
                    "slowk": float(slowk[-1]) if slowk.size > 0 else None,
                    "slowd": float(slowd[-1]) if slowd.size > 0 else None,
                },
                "mfi": float(mfi[-1]) if mfi.size > 0 else None,
                "volatilidade": volatilidade,
            }

            if isinstance(dados_completos, dict):
                dados_completos["osciladores"] = resultado
            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["osciladores"] = resultado_padrao
            return True
