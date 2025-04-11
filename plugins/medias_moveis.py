from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class MediasMoveis(Plugin):
    PLUGIN_NAME = "medias_moveis"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["tendencia", "indicador", "mm"]
    PLUGIN_PRIORIDADE = 40

    def executar(self, *args, **kwargs) -> bool:
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")

        logger.debug(f"Iniciando medias_moveis para {symbol} - {timeframe}")

        resultado_padrao = {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.0,
            "indicadores": {"ma20": None, "ma50": None},
        }

        if not isinstance(dados_completos, dict) or not all([symbol, timeframe]):
            logger.error("Parâmetros inválidos recebidos em medias_moveis")
            if isinstance(dados_completos, dict):
                dados_completos["medias_moveis"] = resultado_padrao
            return True

        dados_crus = dados_completos.get("crus", [])
        if not isinstance(dados_crus, list) or len(dados_crus) < 50:
            logger.warning(f"Dados crus insuficientes para {symbol} - {timeframe}")
            dados_completos["medias_moveis"] = resultado_padrao
            return True

        try:
            sinal = self.gerar_sinal(dados_crus)
            dados_completos["medias_moveis"] = sinal
            logger.info(f"medias_moveis concluído para {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.error(f"Erro ao processar medias_moveis: {e}", exc_info=True)
            dados_completos["medias_moveis"] = resultado_padrao
            return True

    def gerar_sinal(self, crus):
        try:
            closes = self._extrair_dados(crus, [4])[4]
            if len(closes) < 50:
                logger.warning("Menos de 50 candles disponíveis.")
                return self._resultado_padrao()

            ma20 = talib.SMA(closes, timeperiod=20)
            ma50 = talib.SMA(closes, timeperiod=50)

            if ma20[-1] is None or ma50[-1] is None:
                return self._resultado_padrao()

            distancia = abs(ma20[-1] - ma50[-1]) / ma50[-1] * 100
            tendencia_alta = sum(ma20[i] > ma50[i] for i in range(-5, 0))
            tendencia_baixa = sum(ma20[i] < ma50[i] for i in range(-5, 0))

            direcao = (
                "ALTA"
                if tendencia_alta > tendencia_baixa
                else "BAIXA" if tendencia_baixa > tendencia_alta else "LATERAL"
            )
            confianca = (
                round((max(tendencia_alta, tendencia_baixa) / 5) * distancia, 2)
                if direcao != "LATERAL"
                else 0.0
            )
            forca = (
                "FORTE" if confianca >= 70 else "MÉDIA" if confianca >= 30 else "FRACA"
            )

            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "indicadores": {"ma20": round(ma20[-1], 4), "ma50": round(ma50[-1], 4)},
            }
        except Exception as e:
            logger.error(f"Erro ao gerar sinal MM: {e}")
            return self._resultado_padrao()

    def _resultado_padrao(self):
        return {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.0,
            "indicadores": {"ma20": None, "ma50": None},
        }
