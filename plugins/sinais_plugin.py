from utils.logging_config import get_logger
from plugins.plugin import Plugin
import logging

logger = get_logger(__name__)
logger_sinais = logging.getLogger("sinais")


class SinaisPlugin(Plugin):
    """
    Plugin responsável por consolidar dados de análise e gerar o sinal final
    com SL/TP, confiança e alavancagem.
    """

    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["consolidacao", "sinal", "output"]
    PLUGIN_PRIORIDADE = 99

    def __init__(self, calculo_alavancagem=None, calculo_risco=None, **kwargs):
        super().__init__(**kwargs)
        self._calculo_alavancagem = calculo_alavancagem
        self._calculo_risco = calculo_risco

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
            sinais = self._gerar_sinal(dados_completos, symbol, timeframe)
            dados_completos["sinais"] = sinais
            logger.execution(f"Sinais consolidados com sucesso: {sinais}")
            return True
        except Exception as e:
            logger.error(f"Erro na execução do SinaisPlugin: {e}", exc_info=True)
            return False

    def _gerar_sinal(self, dados: dict, symbol: str, timeframe: str) -> dict:
        analise = dados.get("analise_mercado", {})
        direcao = analise.get("direcao", "NEUTRO")
        forca = analise.get("forca", "FRACA")
        confianca_base = analise.get("confianca", 0.0)

        confianca = self._calcular_confianca(dados, direcao, confianca_base)
        alavancagem = self._calcular_alavancagem(dados, direcao, confianca)
        stop_loss, take_profit = self._extrair_sl_tp(dados, direcao)
        timestamp = self._extrair_timestamp(dados)

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

    def _calcular_confianca(self, dados: dict, direcao: str, base: float) -> float:
        """
        Consolida as confiabilidades dos plugins com base na direção.
        """
        confiancas = []
        for info in dados.values():
            if isinstance(info, dict) and "confianca" in info:
                c = info.get("confianca", 0.0)
                if c > 0:
                    confiancas.append(c)
                    dir_info = info.get("direcao")
                    if dir_info == direcao:
                        base += 5
                    elif dir_info and dir_info not in ["NEUTRO", direcao]:
                        base -= 5

        media = sum(confiancas) / len(confiancas) if confiancas else 0.0
        resultado = (base + media) / 2 if confiancas else base
        return max(0.0, min(round(resultado, 2), 100.0))

    def _calcular_alavancagem(self, dados, direcao, confianca) -> float:
        """
        Delega ao plugin de cálculo a decisão de alavancagem. Nenhum valor fixo aqui!
        """
        if not self._calculo_alavancagem:
            logger.warning("Plugin de cálculo de alavancagem não disponível.")
            return 0.0

        try:
            return self._calculo_alavancagem.calcular_alavancagem(
                crus=dados.get("crus", []), direcao=direcao, confianca=confianca
            )
        except Exception as e:
            logger.warning(f"Erro ao calcular alavancagem: {e}")
            return 0.0

    def _extrair_sl_tp(self, dados: dict, direcao: str):
        """
        Retorna stop loss e take profit com base nos padrões de candle.
        """
        esperado = {"ALTA": "compra", "BAIXA": "venda"}.get(direcao)
        padroes = dados.get("candles", {}).get("padroes", {})
        for padrao in padroes.values():
            if padrao.get("sinal") == esperado:
                return padrao.get("stop_loss"), padrao.get("take_profit")
        return None, None

    def _extrair_timestamp(self, dados: dict):
        """
        Retorna o timestamp da última candle disponível.
        """
        crus = dados.get("crus", [])
        return (
            crus[-1][0]
            if crus and isinstance(crus[-1], (list, tuple)) and len(crus[-1]) > 0
            else None
        )
