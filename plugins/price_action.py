from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class PriceAction(Plugin):
    """
    Plugin de análise de price action com reconhecimento de padrões simples de candle,
    baseado em corpo, pavio e direção.
    """

    PLUGIN_NAME = "price_action"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["price_action", "candles", "direcional"]
    PLUGIN_PRIORIDADE = 40

    def executar(self, *args, **kwargs) -> bool:
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos", {})

        resultado_padrao = {
            "price_action": {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "padrao": None,
            }
        }

        if not all([symbol, timeframe, dados_completos]):
            logger.error("Parâmetros obrigatórios ausentes para PriceAction.")
            dados_completos.update(resultado_padrao)
            return False

        klines = dados_completos.get("crus", [])
        if not isinstance(klines, list) or len(klines) < 20:
            logger.warning(
                f"PriceAction ignorado por dados insuficientes para {symbol}-{timeframe}"
            )
            dados_completos.update(resultado_padrao)
            return False

        try:
            sinal = self.gerar_sinal(klines)
            dados_completos["price_action"] = sinal
            logger.info(f"PriceAction concluído para {symbol}-{timeframe}")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar PriceAction: {e}", exc_info=True)
            dados_completos.update(resultado_padrao)
            return False

    def gerar_sinal(self, klines: list) -> dict:
        dados = self._extrair_dados(klines, [1, 2, 3, 4])
        open_, high, low, close = dados[1], dados[2], dados[3], dados[4]

        ultimo = {
            "open": open_[-1],
            "high": high[-1],
            "low": low[-1],
            "close": close[-1],
        }

        padrao = self._identificar_padrao(ultimo)
        direcao = self._analisar_direcao(ultimo)
        forca = self._calcular_forca(ultimo)

        confianca = round(forca * 100, 2) if padrao != "doji" else 0.0
        direcao_final = direcao if direcao != "LATERAL" else "LATERAL"
        forca_label = "FORTE" if forca > 0.7 else "MÉDIA" if forca > 0.3 else "FRACA"

        return {
            "direcao": direcao_final,
            "forca": forca_label,
            "confianca": confianca,
            "padrao": padrao,
        }

    def _identificar_padrao(self, candle: dict) -> str:
        try:
            corpo = abs(candle["close"] - candle["open"])
            range_ = candle["high"] - candle["low"]
            if range_ == 0:
                return "indefinido"
            proporcao = corpo / range_
            if proporcao < 0.1:
                return "doji"
            return "alta" if candle["close"] > candle["open"] else "baixa"
        except Exception as e:
            logger.error(f"Erro ao identificar padrão: {e}")
            return "indefinido"

    def _calcular_forca(self, candle: dict) -> float:
        try:
            corpo = abs(candle["close"] - candle["open"])
            range_ = candle["high"] - candle["low"]
            return round(corpo / range_, 4) if range_ > 0 else 0.0
        except Exception as e:
            logger.error(f"Erro ao calcular força: {e}")
            return 0.0

    def _analisar_direcao(self, candle: dict) -> str:
        try:
            if candle["close"] > candle["open"]:
                return "ALTA"
            elif candle["close"] < candle["open"]:
                return "BAIXA"
            return "LATERAL"
        except Exception as e:
            logger.error(f"Erro ao analisar direção: {e}")
            return "LATERAL"

    def _extrair_dados(self, dados: list, indices: list) -> dict:
        try:
            return {
                i: np.array([float(k[i]) for k in dados], dtype=np.float64)
                for i in indices
            }
        except Exception as e:
            logger.error(f"Erro na extração dos dados: {e}")
            return {i: np.array([]) for i in indices}
