from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
from plugins.plugin import Plugin

import talib
import numpy as np
import pandas as pd

logger = get_logger(__name__)


class IndicadoresVolume(Plugin):
    PLUGIN_NAME = "indicadores_volume"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicador", "volume"]
    PLUGIN_PRIORIDADE = 50

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "periodo_base": 14,
            "periodo_maximo": 28,
            "periodo_minimo": 7,
        }
        logger.debug(f"{self.nome} inicializado")

    def _extrair_dados(self, klines, colunas: list) -> list:
        try:
            dados = list(zip(*klines))
            return [np.array(dados[i], dtype=np.float64) for i in colunas]
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return [np.array([]) for _ in colunas]

    def _ajustar_periodo(self, timeframe: str, volatilidade: float) -> int:
        base = self.config["periodo_base"]
        if timeframe == "1m":
            base = max(self.config["periodo_minimo"], base // 2)
        elif timeframe == "1d":
            base = min(self.config["periodo_maximo"], base * 2)

        base += int(volatilidade * 10)
        return max(
            self.config["periodo_minimo"], min(base, self.config["periodo_maximo"])
        )

    def calcular_obv(self, close: np.ndarray, volume: np.ndarray):
        try:
            return talib.OBV(close, volume)
        except Exception as e:
            logger.error(f"Erro ao calcular OBV: {e}")
            return np.array([])

    def calcular_mfi(self, high, low, close, volume, periodo):
        try:
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"Erro ao calcular MFI: {e}")
            return np.array([])

    def calcular_cmf(self, high, low, close, volume, periodo):
        try:
            money_flow_volume = (
                (2 * close - high - low) / (high - low + 1e-6)
            ) * volume
            mfv_sum = pd.Series(money_flow_volume).rolling(window=periodo).sum()
            vol_sum = pd.Series(volume).rolling(window=periodo).sum()
            cmf = (mfv_sum / (vol_sum + 1e-6)).fillna(0.0)
            return cmf.to_numpy()
        except Exception as e:
            logger.error(f"Erro ao calcular CMF: {e}")
            return np.array([])

    def calcular_volatilidade(self, close, periodo=14) -> float:
        try:
            std = talib.STDDEV(close, timeperiod=periodo)
            return (
                float(std[-1]) / float(close[-1])
                if std.size > 0 and close[-1] != 0
                else 0.0
            )
        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {e}")
            return 0.0

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {"obv": None, "cmf": None, "mfi": None}
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros ausentes para execução de {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["volume"] = resultado_padrao
                return True

            klines = dados_completos.get("crus", [])
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                dados_completos["volume"] = resultado_padrao
                return True

            # Corrigido: [2,3,4,5] retorna [high, low, close, volume]
            high, low, close, volume = self._extrair_dados(klines, [2, 3, 4, 5])

            volatilidade = self.calcular_volatilidade(close)
            periodo = self._ajustar_periodo(timeframe, volatilidade)

            obv = self.calcular_obv(close, volume)
            cmf = self.calcular_cmf(high, low, close, volume, periodo)
            mfi = self.calcular_mfi(high, low, close, volume, periodo)

            resultado = {
                "obv": float(obv[-1]) if obv.size > 0 else None,
                "cmf": float(cmf[-1]) if cmf.size > 0 else None,
                "mfi": float(mfi[-1]) if mfi.size > 0 else None,
            }

            dados_completos["volume"] = resultado
            logger.debug(
                f"[{symbol} - {timeframe}] Indicadores de volume gerados: {resultado}"
            )
            return True

        except Exception as e:
            logger.error(f"Erro na execução de {self.nome}: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos["volume"] = resultado_padrao
            return True
