# analise_candles.py
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin
from utils.padroes_candles import PADROES_CANDLES

logger = get_logger(__name__)


class AnaliseCandles(Plugin):
    PLUGIN_NAME = "analise_candles"
    PLUGIN_TYPE = "adicional"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.cache_padroes = {}

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "candles": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "stop_loss": None,
                "take_profit": None,
                "padrao": None,
            }
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            config = kwargs.get("config", self._config)

            if not all([dados, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            if not isinstance(dados, list) or len(dados) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            sinal = self.gerar_sinal(dados, symbol, timeframe, config)
            if isinstance(dados, dict):
                dados["candles"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar analise_candles: {e}")
            if isinstance(dados, dict):
                dados.update(resultado_padrao)
            return True

    def gerar_sinal(self, dados, symbol, timeframe, config):
        try:
            dados_extraidos = self._extrair_dados(dados, [1, 2, 3, 4, 5])
            open_prices, high, low, close, volume = (
                dados_extraidos[1],
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(close) < 20:
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "stop_loss": None,
                    "take_profit": None,
                    "padrao": None,
                }

            padroes = self._identificar_padroes_talib(open_prices, high, low, close)
            if not padroes:
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "stop_loss": None,
                    "take_profit": None,
                    "padrao": None,
                }

            ultimo_candle = dados[-1]
            alavancagem = config.get("trading", {}).get(
                "alavancagem_maxima", 10
            )  # Default 10x se não houver config
            for padrao_nome, resultado in padroes.items():
                if resultado[-1] != 0:
                    chave_padrao = (
                        f"{padrao_nome}_{'alta' if resultado[-1] > 0 else 'baixa'}"
                    )
                    if chave_padrao not in PADROES_CANDLES:
                        continue

                    padrao_info = PADROES_CANDLES[chave_padrao]
                    direcao = "ALTA" if padrao_info["sinal"] == "compra" else "BAIXA"
                    stop_loss = padrao_info["stop_loss"](ultimo_candle, alavancagem)
                    take_profit = padrao_info["take_profit"](ultimo_candle, alavancagem)
                    forca = self._calcular_forca(dados)
                    confianca = self._calcular_confianca(dados)
                    return {
                        "direcao": direcao,
                        "forca": forca,
                        "confianca": confianca,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "padrao": padrao_nome,
                    }

            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "stop_loss": None,
                "take_profit": None,
                "padrao": None,
            }
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "stop_loss": None,
                "take_profit": None,
                "padrao": None,
            }

    def _identificar_padroes_talib(self, open_prices, high, low, close):
        try:
            padroes = {}
            for nome_funcao in talib.get_function_groups()["Pattern Recognition"]:
                funcao = getattr(talib, nome_funcao)
                resultado = funcao(open_prices, high, low, close)
                if resultado.size:
                    nome_padrao = nome_funcao.lower().replace("cdl", "")
                    padroes[nome_padrao] = resultado
            return padroes
        except Exception as e:
            logger.error(f"Erro ao identificar padrões TA-Lib: {e}")
            return {}

    def _calcular_forca(self, dados):
        try:
            dados_extraidos = self._extrair_dados(dados, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if not close.size or not volume.size:
                return "FRACA"
            variacao_preco = abs(close[-1] - close[-2]) / close[-2]
            volume_relativo = volume[-1] / np.mean(volume)
            forca = variacao_preco * volume_relativo
            return "FORTE" if forca > 0.5 else "MÉDIA" if forca > 0.2 else "FRACA"
        except Exception as e:
            logger.error(f"Erro ao calcular força: {e}")
            return "FRACA"

    def _calcular_confianca(self, dados):
        try:
            dados_extraidos = self._extrair_dados(dados, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if not close.size or not volume.size:
                return 0.0
            volatilidade = np.std(close)
            volume_medio = np.mean(volume)
            confianca = min(
                max((volatilidade * volume_medio) / (100 * volume_medio), 0.0), 1.0
            )
            return confianca * 100
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.0
