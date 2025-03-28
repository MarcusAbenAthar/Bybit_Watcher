# medias_moveis.py
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class MediasMoveis(Plugin):
    PLUGIN_NAME = "medias_moveis"
    PLUGIN_TYPE = "essencial"

    def executar(self, *args, **kwargs) -> bool:
        logger.debug(
            f"Iniciando medias_moveis para {kwargs.get('symbol')} - {kwargs.get('timeframe')}"
        )
        resultado_padrao = {
            "direcao": "NEUTRO",
            "forca": "FRACA",
            "confianca": 0.0,
            "indicadores": {"ma20": None, "ma50": None},
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not isinstance(dados_completos, dict) or not all([symbol, timeframe]):
                logger.error(
                    f"Parâmetros inválidos. Dados: {dados_completos}, Symbol: {symbol}, Timeframe: {timeframe}"
                )
                if isinstance(dados_completos, dict):
                    dados_completos["processados"]["medias_moveis"] = resultado_padrao
                return True

            dados_crus = dados_completos.get("crus")
            if (
                not dados_crus
                or not isinstance(dados_crus, list)
                or len(dados_crus) < 50
            ):
                logger.warning(
                    f"Dados insuficientes para {symbol} - {timeframe}. Crus: {dados_crus}"
                )
                dados_completos["processados"]["medias_moveis"] = resultado_padrao
                return True

            sinal = self.gerar_sinal(dados_crus)
            logger.debug(f"Sinal gerado para {symbol} - {timeframe}: {sinal}")
            dados_completos["processados"]["medias_moveis"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar medias_moveis: {e}")
            dados_completos["processados"]["medias_moveis"] = resultado_padrao
            return True

    def gerar_sinal(self, dados_crus):
        try:
            # Assumindo que dados_crus é uma lista de listas [timestamp, open, high, low, close, volume, ...]
            close = np.array(
                [float(kline[4]) for kline in dados_crus]
            )  # Extrai preços de fechamento
            if len(close) < 50:
                logger.warning(f"menos de 50 klines disponíveis: {len(close)}")
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "indicadores": {"ma20": None, "ma50": None},
                }

            ma20 = talib.SMA(close, timeperiod=20)
            ma50 = talib.SMA(close, timeperiod=50)
            distancia = abs(ma20[-1] - ma50[-1]) / ma50[-1] * 100

            forca = (
                "FORTE"
                if distancia >= 2.0
                else "MÉDIA" if distancia >= 1.0 else "FRACA"
            )
            tendencia_alta = sum(1 for i in range(-5, 0) if ma20[i] > ma50[i])
            tendencia_baixa = sum(1 for i in range(-5, 0) if ma20[i] < ma50[i])

            if tendencia_alta > tendencia_baixa:
                direcao = "ALTA"
                confianca = (tendencia_alta / 5) * 100
            elif tendencia_baixa > tendencia_alta:
                direcao = "BAIXA"
                confianca = (tendencia_baixa / 5) * 100
            else:
                direcao = "NEUTRO"
                confianca = 0.0

            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "indicadores": {"ma20": float(ma20[-1]), "ma50": float(ma50[-1])},
            }
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {"ma20": None, "ma50": None},
            }
