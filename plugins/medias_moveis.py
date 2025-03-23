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
        resultado_padrao = {
            "medias_moveis": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {"ma20": None, "ma50": None},
            }
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            if not isinstance(dados, list) or len(dados) < 50:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            sinal = self.gerar_sinal(dados)
            if isinstance(dados, dict):
                dados["medias_moveis"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar medias_moveis: {e}")
            if isinstance(dados, dict):
                dados.update(resultado_padrao)
            return True

    def gerar_sinal(self, dados):
        try:
            dados_extraidos = self._extrair_dados(dados, [4])
            close = dados_extraidos[4]
            if len(close) < 50:
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
