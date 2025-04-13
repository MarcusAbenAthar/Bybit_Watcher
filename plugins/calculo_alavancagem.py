"""
Plugin responsável por calcular alavancagem com base na volatilidade (ATR) e na confiança do sinal.
Autonomia + critério + segurança, com 100% de aderência à configuração externa.
"""

from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
from utils.config import carregar_config
import numpy as np
import talib

logger = get_logger(__name__)


class CalculoAlavancagem(Plugin):
    PLUGIN_NAME = "calculo_alavancagem"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "volatilidade", "alavancagem"]
    PLUGIN_PRIORIDADE = 85

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self._config = carregar_config()
        self._alav_max = self._config["trading"]["alavancagem_maxima"]
        self._alav_min = self._config["trading"]["alavancagem_minima"]

    def calcular_alavancagem(
        self, crus: list, direcao: str = None, confianca: float = 0.0
    ) -> float:
        """
        Calcula a alavancagem com base no ATR (volatilidade) e na confiança do sinal.
        Retorna uma alavancagem ajustada, limitada pelos valores definidos na configuração.
        """
        if not crus or len(crus) < 14:
            logger.warning("Candles insuficientes para cálculo de alavancagem.")
            return self._alav_min

        try:
            highs = np.array([float(c[2]) for c in crus], dtype=np.float64)
            lows = np.array([float(c[3]) for c in crus], dtype=np.float64)
            closes = np.array([float(c[4]) for c in crus], dtype=np.float64)

            atr = talib.ATR(highs, lows, closes, timeperiod=14)

            if atr is None or atr.size == 0 or closes[-1] == 0:
                logger.warning("ATR inválido ou preço atual zerado.")
                return self._alav_min

            atr_atual = atr[-1]
            preco_atual = closes[-1]
            volatilidade = atr_atual / preco_atual

            # Define alavancagem base com base na volatilidade
            if volatilidade < 0.001:
                alav_base = self._alav_max
            elif volatilidade < 0.005:
                alav_base = (self._alav_max + self._alav_min) / 2
            else:
                alav_base = self._alav_min

            try:
                confianca = float(confianca)
            except (ValueError, TypeError):
                logger.warning(
                    f"Confiança inválida: {confianca}, aplicando fallback 0.0."
                )
                confianca = 0.0

            fator_conf = confianca / 100 if confianca > 0 else 0.3
            alav_final = alav_base * fator_conf

            if direcao == "NEUTRO":
                logger.info("Direção NEUTRO detectada — alavancagem mínima forçada.")
                return self._alav_min

            resultado = round(max(self._alav_min, min(alav_final, self._alav_max)), 2)

            logger.debug(
                f"Alavancagem final: {resultado}x | Vol: {volatilidade:.5f} | Conf: {confianca:.1f}%"
            )

            return resultado

        except Exception as e:
            logger.error(f"Erro ao calcular alavancagem: {e}", exc_info=True)
            return self._alav_min

    def executar(self, *args, **kwargs) -> bool:
        """
        Método executado pelo sistema principal. Injeta a alavancagem nos dados_completos.
        """
        resultado_padrao = {"alavancagem": self._alav_min}

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros obrigatórios ausentes.")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            crus = dados_completos.get("crus", [])
            if not isinstance(crus, list) or len(crus) < 14:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}.")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            direcao = kwargs.get("direcao", None)
            confianca = kwargs.get("confianca", 0.0)

            alavancagem = self.calcular_alavancagem(
                crus, direcao=direcao, confianca=confianca
            )

            if isinstance(dados_completos, dict):
                dados_completos["alavancagem"] = alavancagem
                logger.debug(
                    f"Alavancagem atribuída para {symbol}-{timeframe}: {alavancagem}x"
                )

            return True

        except Exception as e:
            logger.error(f"Erro ao executar plugin: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True
