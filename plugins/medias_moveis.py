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
                    dados_completos["medias_moveis"] = resultado_padrao
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
                dados_completos["medias_moveis"] = resultado_padrao
                return True

            sinal = self.gerar_sinal(dados_crus)
            logger.debug(f"Sinal gerado para {symbol} - {timeframe}: {sinal}")
            dados_completos["medias_moveis"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar medias_moveis: {e}")
            dados_completos["medias_moveis"] = resultado_padrao
            return True

    def _extrair_dados(self, dados_completos, indices):
        try:
            valores = {idx: [] for idx in indices}
            for candle in dados_completos:
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

    def gerar_sinal(self, dados_crus):
        try:
            dados_extraidos = self._extrair_dados(dados_crus, [4])  # Apenas close
            close = dados_extraidos[4]
            if len(close) < 50:
                logger.warning(f"Menos de 50 klines disponíveis: {len(close)}")
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
