from utils.logging_config import get_logger
from typing import Dict, Optional, Any
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

    _RESULTADO_PADRAO = {
        "analise_mercado": {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.0,
        }
    }

    def inicializar(self, config: Dict[str, Any]) -> bool:
        if not super().inicializar(config):
            return False
        logger.info(
            f"{self.nome} inicializado com timeframes: {self._config.get('timeframes')}"
        )
        return True

    def executar(self, *args, **kwargs) -> bool:
        dados_completos = kwargs.get("dados_completos")
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")

        if not all([dados_completos, symbol, timeframe]):
            logger.error(f"{self.nome}: Parâmetros necessários ausentes.")
            if isinstance(dados_completos, dict):
                dados_completos.update(self._RESULTADO_PADRAO)
            return True

        try:
            resultados = self._coletar_resultados(dados_completos)
            consolidado = self._consolidar_resultados(resultados)
            dados_completos["analise_mercado"] = consolidado

            logger.debug(
                f"{self.nome} -> {symbol}-{timeframe} consolidação: {consolidado}"
            )
            return True

        except Exception as e:
            logger.error(f"{self.nome}: Erro na execução: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos.update(self._RESULTADO_PADRAO)
            return True

    def _coletar_resultados(
        self, dados: Dict[str, Any]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        fontes = ["price_action", "medias_moveis", "tendencia", "candles"]
        padrao = {"direcao": "LATERAL", "forca": "FRACA", "confianca": 0.0}
        resultados = {}

        for fonte in fontes:
            resultado = dados.get(fonte)
            if not isinstance(resultado, dict):
                logger.warning(f"{self.nome}: Resultado inválido para fonte '{fonte}'")
                resultado = padrao
            resultados[fonte] = {
                "direcao": resultado.get("direcao", "LATERAL"),
                "forca": resultado.get("forca", "FRACA"),
                "confianca": resultado.get("confianca", 0.0) or 0.0,
            }

        return resultados

    def _consolidar_resultados(
        self, resultados: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        direcoes = []
        confiancas = []

        for nome, r in resultados.items():
            direcao = r.get("direcao", "LATERAL")
            confianca = r.get("confianca", 0.0)

            logger.debug(
                f"{self.nome} -> {nome}: direção={direcao}, confiança={confianca}"
            )

            if direcao != "LATERAL":
                direcoes.append(direcao)
                confiancas.append(confianca)

        if not direcoes:
            return self._RESULTADO_PADRAO["analise_mercado"]

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
