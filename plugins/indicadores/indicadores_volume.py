# indicadores_volume.py
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
import pandas as pd
from pandas_ta import volume
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresVolume(Plugin):
    PLUGIN_NAME = "indicadores_volume"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerentePlugin, config=None):
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.config = config or {}
        self.gerente = gerente
        self.banco_dados = self.gerente.obter_plugin("banco_dados")
        logger.debug("IndicadoresVolume inicializado")

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
                logger.warning("Dados insuficientes ou inválidos em _extrair_dados")
                return {idx: np.array([]) for idx in indices}
            return {idx: np.array(valores[idx], dtype=np.float64) for idx in indices}
        except Exception as e:
            logger.error(f"Erro ao extrair dados_crus: {e}")
            return {idx: np.array([]) for idx in indices}

    def calcular_obv(self, dados_crus):
        try:
            dados_extraidos = self._extrair_dados(dados_crus, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if len(close) < 2:
                return np.array([])
            return talib.OBV(close, volume)
        except Exception as e:
            logger.error(f"Erro ao calcular OBV: {e}")
            return np.array([])

    def calcular_mfi(self, dados_crus, periodo=14):
        try:
            dados_extraidos = self._extrair_dados(dados_crus, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(high) < periodo:
                return np.array([])
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"Erro ao calcular MFI: {e}")
            return np.array([])

    def executar(self, *args, **kwargs) -> bool:
        logger.debug(
            f"Iniciando indicadores_volume para {kwargs.get('symbol')} - {kwargs.get('timeframe')}"
        )
        resultado_padrao = {
            "obv": None,
            "cmf": None,
            "mfi": None,
            "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                dados_completos["processados"]["indicadores_volume"] = resultado_padrao
                return True

            dados_crus = dados_completos.get("crus")
            if (
                not dados_crus
                or not isinstance(dados_crus, list)
                or len(dados_crus) < 20
            ):
                logger.warning(
                    f"Dados insuficientes para {symbol} - {timeframe}. Crus: {dados_crus}"
                )
                dados_completos["processados"]["indicadores_volume"] = resultado_padrao
                return True

            # Converte dados_crus pra DataFrame pro pandas-ta
            df = pd.DataFrame(
                dados_crus,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df = df.astype(
                {"high": float, "low": float, "close": float, "volume": float}
            )

            # Calcula indicadores
            obv = self.calcular_obv(dados_crus)
            cmf = volume.cmf(
                df["high"], df["low"], df["close"], df["volume"], length=20
            )
            mfi = self.calcular_mfi(dados_crus)

            resultado = {
                "obv": float(obv[-1]) if obv.size > 0 else None,
                "cmf": float(cmf.iloc[-1]) if not cmf.empty else None,
                "mfi": float(mfi[-1]) if mfi.size > 0 else None,
                "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
            }

            logger.debug(f"Sinal gerado para {symbol} - {timeframe}: {resultado}")
            dados_completos["processados"]["indicadores_volume"] = resultado

            if self.banco_dados and hasattr(self.banco_dados, "conn"):
                try:
                    timestamp = int(dados_crus[-1][0] / 1000)
                    cursor = self.banco_dados.conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO indicadores_volume (
                            symbol, timeframe, timestamp, obv, cmf, mfi
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) 
                        DO UPDATE SET
                            obv = EXCLUDED.obv,
                            cmf = EXCLUDED.cmf,
                            mfi = EXCLUDED.mfi
                        """,
                        (
                            symbol,
                            timeframe,
                            timestamp,
                            resultado["obv"],
                            resultado["cmf"],
                            resultado["mfi"],
                        ),
                    )
                    self.banco_dados.conn.commit()
                    logger.debug(f"Dados salvos no banco para {symbol} - {timeframe}")
                except Exception as e:
                    logger.error(f"Erro ao salvar no banco: {e}")

            return True
        except Exception as e:
            logger.error(f"Erro ao executar indicadores_volume: {e}")
            dados_completos["processados"]["indicadores_volume"] = resultado_padrao
            return True
