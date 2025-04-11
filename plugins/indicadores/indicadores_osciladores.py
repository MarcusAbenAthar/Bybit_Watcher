# indicadores_osciladores.py

from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresOsciladores(Plugin):
    PLUGIN_NAME = "indicadores_osciladores"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["osciladores", "rsi", "stoch", "mfi"]

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente

    def calcular_rsi(self, klines, symbol, timeframe, base_periodo=14) -> np.ndarray:
        try:
            close = self._extrair_dados(klines, [4])[4]
            if close.size < 10:
                return np.array([])

            volatilidade = self._calcular_volatilidade(close)
            ajuste = int(volatilidade * 10)

            if timeframe == "1m":
                base_periodo = max(7, base_periodo // 2)
            elif timeframe == "1d":
                base_periodo = min(28, base_periodo * 2)

            periodo_final = max(7, min(28, base_periodo + ajuste))
            rsi = talib.RSI(close, timeperiod=periodo_final)
            return rsi
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular RSI: {e}")
            return np.array([])

    def calcular_estocastico(self, klines, timeframe) -> tuple:
        try:
            extr = self._extrair_dados(klines, [2, 3, 4])
            high, low, close = extr[2], extr[3], extr[4]

            if len(close) < 10:
                return np.array([]), np.array([])

            vol = self._calcular_volatilidade(close)
            ajuste = int(vol * 3)

            base = {"fastk": 5, "slowk": 3, "slowd": 3}
            if timeframe == "1m":
                base = {k: max(2, v // 2) for k, v in base.items()}
            elif timeframe == "1d":
                base = {k: min(10, v * 2) for k, v in base.items()}

            fastk = max(3, min(10, base["fastk"] + ajuste))
            slowk = max(2, min(6, base["slowk"] + ajuste))
            slowd = max(2, min(6, base["slowd"] + ajuste))

            slowk_vals, slowd_vals = talib.STOCH(
                high,
                low,
                close,
                fastk_period=fastk,
                slowk_period=slowk,
                slowk_matype=0,
                slowd_period=slowd,
                slowd_matype=0,
            )
            return slowk_vals, slowd_vals
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular Estocástico: {e}")
            return np.array([]), np.array([])

    def calcular_mfi(self, klines, periodo=14) -> np.ndarray:
        try:
            extr = self._extrair_dados(klines, [2, 3, 4, 5])
            high, low, close, volume = extr[2], extr[3], extr[4], extr[5]
            if len(close) < periodo:
                return np.array([])
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular MFI: {e}")
            return np.array([])

    def _calcular_volatilidade(self, close, periodo=14) -> float:
        try:
            if len(close) < periodo:
                return 0.0
            stddev = talib.STDDEV(close, timeperiod=periodo)
            return (
                round(min(max(stddev[-1] / close[-1], 0.0), 1.0), 4)
                if stddev.size
                else 0.0
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular volatilidade: {e}")
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
                logger.error(f"Parâmetros ausentes em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["osciladores"] = resultado_padrao
                return True

            crus = dados_completos.get("crus", [])
            if not isinstance(crus, list) or len(crus) < 20:
                logger.warning(f"[{self.nome}] Dados crus insuficientes")
                dados_completos["osciladores"] = resultado_padrao
                return True

            rsi = self.calcular_rsi(crus, symbol, timeframe)
            slowk, slowd = self.calcular_estocastico(crus, timeframe)
            mfi = self.calcular_mfi(crus)
            close = self._extrair_dados(crus, [4])[4]
            volatilidade = self._calcular_volatilidade(close)

            resultado = {
                "rsi": float(rsi[-1]) if rsi.size else None,
                "estocastico": {
                    "slowk": float(slowk[-1]) if slowk.size else None,
                    "slowd": float(slowd[-1]) if slowd.size else None,
                },
                "mfi": float(mfi[-1]) if mfi.size else None,
                "volatilidade": volatilidade,
            }

            dados_completos["osciladores"] = resultado
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["osciladores"] = resultado_padrao
            return True
