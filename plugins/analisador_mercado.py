from utils.logging_config import get_logger
from typing import Dict, Optional
from plugins.plugin import Plugin

logger = get_logger(__name__)


class AnalisadorMercado(Plugin):
    """
    Plugin que consolida os sinais dos demais módulos para gerar
    uma visão unificada da direção de mercado.
    """

    PLUGIN_NAME = "analisador_mercado"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "consolidacao", "direcional"]
    PLUGIN_PRIORIDADE = 80

    def inicializar(self, config: Dict) -> bool:
        if not super().inicializar(config):
            return False
        logger.info(
            f"{self.nome} inicializado com timeframes: {self._config.get('timeframes')}"
        )
        return True

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "analise_mercado": {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
            }
        }

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros necessários ausentes")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            resultados = self._coletar_resultados(dados_completos)
            consolidado = self._consolidar_resultados(resultados)
            dados_completos["analise_mercado"] = consolidado

            logger.debug(f"Consolidação {symbol}-{timeframe}: {consolidado}")
            return True

        except Exception as e:
            logger.error(f"Erro no analisador_mercado: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _coletar_resultados(self, dados: Dict) -> Dict[str, Dict[str, Optional[float]]]:
        fontes = ["price_action", "medias_moveis", "tendencia", "candles"]
        padrao = {"direcao": "LATERAL", "forca": "FRACA", "confianca": 0.0}
        return {fonte: dados.get(fonte, padrao) for fonte in fontes}

    def _consolidar_resultados(self, resultados: Dict[str, Dict]) -> Dict[str, object]:
        direcoes = []
        confiancas = []

        for nome, r in resultados.items():
            direcao = r.get("direcao", "LATERAL")
            confianca = r.get("confianca", 0.0)
            logger.debug(f"{nome}: direção={direcao}, confiança={confianca}")

            if direcao != "LATERAL":
                direcoes.append(direcao)
                confiancas.append(confianca)

        if not direcoes:
            return {"direcao": "LATERAL", "forca": "FRACA", "confianca": 0.0}

        direcao_final = max(set(direcoes), key=direcoes.count)
        qtd_confirmacoes = direcoes.count(direcao_final)
        total_plugins = len(resultados)
        confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0.0

        peso = qtd_confirmacoes / total_plugins
        confianca_final = round(confianca_media * peso, 2)

        forca = (
            "FORTE"
            if qtd_confirmacoes >= 3
            else "MÉDIA" if qtd_confirmacoes == 2 else "FRACA"
        )

        return {
            "direcao": direcao_final,
            "forca": forca,
            "confianca": confianca_final,
        }
