# analise_candles.py
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin
from utils.padroes_candles import PADROES_CANDLES

logger = get_logger(__name__)


class AnaliseCandles(Plugin):
    PLUGIN_NAME = "analise_candles"
    PLUGIN_TYPE = "essencial"

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
                "padrao": None,
            }
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            config = kwargs.get("config", self._config)

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            klines = dados_completos.get("crus", [])
            logger.debug(
                f"Verificando klines para {symbol} - {timeframe}, tamanho: {len(klines)}"
            )
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            sinal = self.gerar_sinal(klines, symbol, timeframe, config)
            logger.info(f"Sinal gerado para {symbol} - {timeframe}: {sinal}")
            if isinstance(dados_completos, dict):
                dados_completos["candles"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar analise_candles: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def gerar_sinal(self, dados_completos, symbol, timeframe, config):
        try:
            logger.debug(f"Iniciando geração de sinal para {symbol} - {timeframe}")
            dados_extraidos = self._extrair_dados(dados_completos, [1, 2, 3, 4, 5])
            open_prices, high, low, close, volume = (
                dados_extraidos[1],
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            logger.debug(f"Dados extraídos: {len(close)} candles")
            if len(close) < 20:
                logger.warning(f"Menos de 20 candles para {symbol} - {timeframe}")
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "padrao": None,
                }

            padroes = self._identificar_padroes_talib(open_prices, high, low, close)
            logger.debug(f"Padrões identificados: {list(padroes.keys())}")
            if not padroes:
                logger.debug(f"Nenhum padrão encontrado para {symbol} - {timeframe}")
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "padrao": None,
                }

            # Verificar padrão no candle anterior
            for padrao_nome, resultado in padroes.items():
                if len(resultado) >= 2 and resultado[-2] != 0:  # Candle anterior
                    chave_padrao = (
                        f"{padrao_nome}_{'alta' if resultado[-2] > 0 else 'baixa'}"
                    )
                    if chave_padrao not in PADROES_CANDLES:
                        logger.debug(
                            f"Padrão {chave_padrao} não mapeado em PADROES_CANDLES"
                        )
                        continue

                    padrao_info = PADROES_CANDLES[chave_padrao]
                    direcao = "ALTA" if padrao_info["sinal"] == "compra" else "BAIXA"
                    logger.info(
                        f"Padrão {padrao_nome} detectado no candle anterior para {symbol} - {timeframe}"
                    )
                    forca = self._calcular_forca(dados_completos)
                    confianca = self._calcular_confianca(dados_completos)
                    return {
                        "direcao": direcao,
                        "forca": forca,
                        "confianca": confianca,
                        "padrao": padrao_nome,
                    }

            logger.debug(
                f"Nenhum padrão ativo encontrado no candle anterior para {symbol} - {timeframe}"
            )
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "padrao": None,
            }
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
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

    def _calcular_forca(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if not close.size or not volume.size:
                return "FRACA"
            variacao_preco = abs(close[-1] - close[-2]) / close[-2]
            volume_relativo = (
                volume[-1] / np.mean(volume[-10:]) if len(volume) >= 10 else 1.0
            )
            forca = variacao_preco * volume_relativo
            return "FORTE" if forca > 0.5 else "MÉDIA" if forca > 0.2 else "FRACA"
        except Exception as e:
            logger.error(f"Erro ao calcular força: {e}")
            return "FRACA"

    def _calcular_confianca(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if not close.size or not volume.size or np.mean(volume[-10:]) == 0:
                return 0.0
            volatilidade = (
                np.std(close[-10:]) / np.mean(close[-10:]) if len(close) >= 10 else 0.0
            )
            volume_relativo = (
                volume[-1] / np.mean(volume[-10:]) if len(volume) >= 10 else 1.0
            )
            confianca = min(max(volatilidade * volume_relativo * 100, 0.0), 100.0)
            return round(confianca, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.0

    def _extrair_dados(self, dados, indices):
        try:
            return {i: np.array([d[i] for d in dados]) for i in indices}
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return {i: np.array([]) for i in indices}
