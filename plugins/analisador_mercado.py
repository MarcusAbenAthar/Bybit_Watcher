# analisador_mercado.py
from utils.logging_config import get_logger
from typing import Dict
from plugins.plugin import Plugin

logger = get_logger(__name__)


class AnalisadorMercado(Plugin):
    PLUGIN_NAME = "analisador_mercado"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente

    def inicializar(self, config: Dict) -> bool:
        if not super().inicializar(config):
            return False
        logger.info(
            "AnalisadorMercado inicializado com timeframes do config: %s",
            self._config["timeframes"],
        )
        return True

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "analise_mercado": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            config = kwargs.get("config", self._config)

            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            if not isinstance(dados_completos, dict):
                logger.warning(
                    f"Dados devem ser um dicionário para {symbol} - {timeframe}"
                )
                return True

            resultados = self._executar_analises(
                dados_completos, symbol, timeframe, config
            )
            dados_completos.update(resultados)
            return True
        except Exception as e:
            logger.error(f"Erro ao executar analisador_mercado: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _executar_analises(
        self, dados_completos: Dict, symbol: str, timeframe: str, config: Dict
    ) -> Dict:
        try:
            # Pegar resultados já processados pelos plugins anteriores
            resultados = {
                "candles": dados_completos.get(
                    "candles", {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
                ),
                "medias_moveis": dados_completos.get(
                    "medias_moveis",
                    {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
                ),
                "price_action": dados_completos.get(
                    "price_action",
                    {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
                ),
                "tendencia": dados_completos.get(
                    "tendencia",
                    {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
                ),
            }

            direcao, forca, confianca = self._consolidar_resultados(resultados)
            return {
                "analise_mercado": {
                    "direcao": direcao,
                    "forca": forca,
                    "confianca": confianca,
                }
            }
        except Exception as e:
            logger.error(f"Erro ao executar análises: {e}")
            return {
                "analise_mercado": {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                }
            }

    def _consolidar_resultados(self, resultados: Dict) -> tuple:
        try:
            direcoes = [r["direcao"] for r in resultados.values()]
            confiancas = [r["confianca"] for r in resultados.values()]
            total_confirmacoes = sum(1 for d in direcoes if d != "NEUTRO")
            if total_confirmacoes == 0:
                return "NEUTRO", "FRACA", 0.0

            direcao_predominante = max(set(direcoes), key=direcoes.count)
            if direcao_predominante == "NEUTRO":
                return "NEUTRO", "FRACA", 0.0

            confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0.0
            forca = (
                "FORTE"
                if total_confirmacoes >= 3
                else "MÉDIA" if total_confirmacoes == 2 else "FRACA"
            )
            return direcao_predominante, forca, confianca_media
        except Exception as e:
            logger.error(f"Erro ao consolidar resultados: {e}")
            return "NEUTRO", "FRACA", 0.0
