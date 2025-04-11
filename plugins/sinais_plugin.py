from utils.logging_config import get_logger
from plugins.plugin import Plugin
import logging

logger = get_logger(__name__)
logger_sinais = logging.getLogger("sinais")


class SinaisPlugin(Plugin):
    """
    Plugin responsável por consolidar dados de análise e gerar o sinal final com SL/TP, confiança e alavancagem.
    """

    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["consolidacao", "sinal", "output"]
    PLUGIN_PRIORIDADE = 99

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def inicializar(self, config: dict) -> bool:
        return super().inicializar(config)

    def executar(self, *args, **kwargs) -> bool:
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos", {})
        config = kwargs.get("config", self._config)

        if not all([symbol, timeframe, dados_completos]):
            logger.error("Parâmetros obrigatórios ausentes para SinaisPlugin.")
            return False

        try:
            logger.execution(f"SinaisPlugin processando {symbol} - {timeframe}")
            sinais = self._consolidar_sinais(dados_completos, symbol, timeframe, config)
            dados_completos["sinais"] = sinais
            logger.execution(f"Sinais consolidados com sucesso: {sinais}")
            return True
        except Exception as e:
            logger.error(f"Erro na execução do SinaisPlugin: {e}", exc_info=True)
            return False

    def _consolidar_sinais(
        self, dados: dict, symbol: str, timeframe: str, config: dict
    ) -> dict:
        analise = dados.get("analise_mercado", {})
        direcao = analise.get("direcao", "NEUTRO")
        forca = analise.get("forca", "FRACA")
        confianca_base = analise.get("confianca", 0.0)

        confiancas = []
        for chave, info in dados.items():
            if isinstance(info, dict) and "confianca" in info:
                confianca = info.get("confianca", 0.0)
                if confianca > 0:
                    confiancas.append(confianca)
                    if info.get("direcao") == direcao:
                        confianca_base += 5
                    elif info.get("direcao") not in [direcao, "NEUTRO"]:
                        confianca_base -= 5

        if confiancas:
            media = sum(confiancas) / len(confiancas)
            confianca = (confianca_base + media) / 2
        else:
            confianca = confianca_base

        confianca = max(0.0, min(round(confianca, 2), 100.0))

        alavancagem = 0.0
        plugin_alav = self._gerente.obter_plugin("plugins.calculo_alavancagem")
        if plugin_alav:
            alavancagem = plugin_alav.calcular_alavancagem(
                dados["crus"],
                direcao=direcao,
                confianca=confianca,
                alavancagem_maxima=config["trading"]["alavancagem_maxima"],
                alavancagem_minima=config["trading"]["alavancagem_minima"],
            )

        resultado_candles = dados.get("candles", {})
        padroes = resultado_candles.get("padroes", {})
        stop_loss, take_profit = None, None

        if padroes:
            esperado = {"ALTA": "compra", "BAIXA": "venda"}.get(direcao)
            for padrao in padroes.values():
                if padrao.get("sinal") == esperado:
                    stop_loss = padrao.get("stop_loss")
                    take_profit = padrao.get("take_profit")
                    break

        timestamp = dados["crus"][-1][0] if dados.get("crus") else None

        sinal = {
            "direcao": direcao,
            "forca": forca,
            "confianca": confianca,
            "alavancagem": alavancagem,
            "timestamp": timestamp,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }

        logger_sinais.info(
            f"[{symbol} - {timeframe}] DIREÇÃO: {direcao} | FORÇA: {forca} | "
            f"CONFIANÇA: {confianca} | ALAVANCAGEM: {alavancagem}x | SL: {stop_loss} | TP: {take_profit}"
        )

        return sinal
