from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
import talib
import numpy as np
import pandas_ta as ta
import pandas as pd

from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresVolume(Plugin):
    PLUGIN_NAME = "indicadores_volume"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "mfi_periodo": 14,
            "cmf_periodo": 20,
        }
        logger.debug(f"{self.nome} inicializado")

    def _extrair_dados(self, dados_crus, indices):
        try:
            valores = {idx: [] for idx in indices}
            for candle in dados_crus:
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

    def calcular_obv(self, dados_crus):
        try:
            dados_extraidos = self._extrair_dados(dados_crus, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if len(close) < 2:
                logger.warning(f"Dados insuficientes para OBV: {len(close)}")
                return np.array([])
            return talib.OBV(close, volume)
        except Exception as e:
            logger.error(f"Erro ao calcular OBV: {e}")
            return np.array([])

    def calcular_mfi(self, dados_crus):
        try:
            dados_extraidos = self._extrair_dados(dados_crus, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(high) < self.config["mfi_periodo"]:
                logger.warning(
                    f"Dados insuficientes para MFI: {len(high)}/{self.config['mfi_periodo']}"
                )
                return np.array([])
            return talib.MFI(
                high, low, close, volume, timeperiod=self.config["mfi_periodo"]
            )
        except Exception as e:
            logger.error(f"Erro ao calcular MFI: {e}")
            return np.array([])

    def calcular_cmf(self, dados_crus):
        try:
            dados_extraidos = self._extrair_dados(dados_crus, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(high) < self.config["cmf_periodo"]:
                logger.warning(
                    f"Dados insuficientes para CMF: {len(high)}/{self.config['cmf_periodo']}"
                )
                return np.array([])

            df = pd.DataFrame(
                {"high": high, "low": low, "close": close, "volume": volume}
            )
            cmf = df.ta.cmf(
                high="high",
                low="low",
                close="close",
                volume="volume",
                length=self.config["cmf_periodo"],
            )
            cmf_array = cmf.to_numpy()
            cmf_array = np.nan_to_num(cmf_array, nan=0.0)
            return cmf_array

        except Exception as e:
            logger.error(f"Erro ao calcular CMF: {e}")
            return np.array([])

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "obv": None,
            "cmf": None,
            "mfi": None,
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos["volume"] = resultado_padrao
                return True

            klines = (
                dados_completos.get("crus", [])
                if isinstance(dados_completos, dict)
                else dados_completos
            )
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos["volume"] = resultado_padrao
                return True

            obv = self.calcular_obv(klines)
            cmf = self.calcular_cmf(klines)
            mfi = self.calcular_mfi(klines)

            resultado = {
                "obv": float(obv[-1]) if obv.size > 0 else None,
                "cmf": float(cmf[-1]) if cmf.size > 0 else None,
                "mfi": float(mfi[-1]) if mfi.size > 0 else None,
            }

            if isinstance(dados_completos, dict):
                dados_completos["volume"] = resultado
                logger.debug(
                    f"Indicadores de volume calculados para {symbol} - {timeframe}"
                )
            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["volume"] = resultado_padrao
            return True
