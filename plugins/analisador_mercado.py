from utils.logging_config import get_logger
from typing import Dict, Optional, Any
from plugins.plugin import Plugin
from copy import deepcopy

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

    FONTES_PADRAO = ["price_action", "medias_moveis", "tendencia", "candles"]
    MINIMO_FONTES = 2  # Mínimo de fontes válidas para consolidação

    def inicializar(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações (ex.: timeframes, fontes).

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        if not super().inicializar(config):
            return False
        self.fontes = config.get("fontes", self.FONTES_PADRAO)
        if not self.fontes or not isinstance(self.fontes, list):
            logger.warning(
                f"[{self.nome}] Fontes inválidas, usando padrão: {self.FONTES_PADRAO}"
            )
            self.fontes = self.FONTES_PADRAO
        logger.info(
            f"[{self.nome}] inicializado com timeframes: {self._config.get('timeframes')}, fontes: {self.fontes}"
        )
        return True

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a consolidação dos sinais e armazena o resultado.

        Args:
            dados_completos (dict): Dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        dados_completos = kwargs.get("dados_completos")
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")

        if not all([dados_completos, symbol, timeframe]):
            logger.error(f"[{self.nome}] Parâmetros necessários ausentes")
            if isinstance(dados_completos, dict):
                self._aplicar_resultado_padrao(dados_completos)
            return True

        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            dados_completos["analise_mercado"] = deepcopy(
                self._RESULTADO_PADRAO["analise_mercado"]
            )
            return True

        try:
            resultados = self._coletar_resultados(dados_completos)
            if len(resultados) < self.MINIMO_FONTES:
                logger.error(
                    f"[{self.nome}] Menos de {self.MINIMO_FONTES} fontes válidas para {symbol}-{timeframe}"
                )
                dados_completos["analise_mercado"] = deepcopy(
                    self._RESULTADO_PADRAO["analise_mercado"]
                )
                return True

            consolidado = self._consolidar_resultados(resultados)
            dados_completos["analise_mercado"] = consolidado

            logger.debug(
                f"[{self.nome}] {symbol}-{timeframe} consolidação: {consolidado}"
            )
            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro na execução: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                self._aplicar_resultado_padrao(dados_completos)
            return True

    def _aplicar_resultado_padrao(self, destino: dict) -> None:
        """
        Aplica o resultado padrão ao dicionário de destino.

        Args:
            destino: Dicionário onde o resultado será armazenado.
        """
        destino.update(deepcopy(self._RESULTADO_PADRAO))

    def _validar_resultado_fonte(self, resultado: Any, fonte: str) -> Dict[str, Any]:
        """
        Valida o formato e tipo do resultado de uma fonte.

        Args:
            resultado: Resultado da fonte.
            fonte: Nome da fonte.

        Returns:
            dict: Resultado validado ou padrão se inválido.
        """
        padrao = {"direcao": "LATERAL", "forca": "FRACA", "confianca": 0.0}
        if not isinstance(resultado, dict):
            logger.warning(
                f"[{self.nome}] Resultado inválido para fonte '{fonte}': não é dicionário"
            )
            return padrao

        direcao = resultado.get("direcao", "LATERAL")
        if direcao not in ["ALTA", "BAIXA", "LATERAL"]:
            logger.warning(f"[{self.nome}] Direção inválida para '{fonte}': {direcao}")
            direcao = "LATERAL"

        forca = resultado.get("forca", "FRACA")
        if forca not in ["FORTE", "MÉDIA", "FRACA"]:
            logger.warning(f"[{self.nome}] Força inválida para '{fonte}': {forca}")
            forca = "FRACA"

        try:
            confianca = float(resultado.get("confianca", 0.0))
            confianca = max(0.0, min(1.0, confianca))
        except (TypeError, ValueError):
            logger.warning(
                f"[{self.nome}] Confiança inválida para '{fonte}': {resultado.get('confianca')}"
            )
            confianca = 0.0

        return {
            "direcao": direcao,
            "forca": forca,
            "confianca": confianca,
        }

    def _coletar_resultados(
        self, dados: Dict[str, Any]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Coleta resultados das fontes especificadas.

        Args:
            dados: Dicionário com dados processados.

        Returns:
            dict: Resultados validados por fonte.
        """
        resultados = {}
        for fonte in self.fontes:
            if fonte not in dados:
                logger.warning(
                    f"[{self.nome}] Fonte '{fonte}' não encontrada em dados_completos"
                )
                continue
            resultado = dados.get(fonte)
            resultados[fonte] = self._validar_resultado_fonte(resultado, fonte)

        return resultados

    def _consolidar_resultados(
        self, resultados: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Consolida os resultados das fontes em uma análise unificada.

        Args:
            resultados: Dicionário com resultados por fonte.

        Returns:
            dict: Resultado consolidado (direcao, forca, confianca).
        """
        direcoes = []
        confiancas = []

        for nome, r in resultados.items():
            direcao = r.get("direcao", "LATERAL")
            confianca = r.get("confianca", 0.0)

            logger.debug(
                f"[{self.nome}] {nome}: direção={direcao}, confiança={confianca}"
            )

            if direcao != "LATERAL":
                direcoes.append(direcao)
                confiancas.append(confianca)

        if not direcoes:
            return deepcopy(self._RESULTADO_PADRAO["analise_mercado"])

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
