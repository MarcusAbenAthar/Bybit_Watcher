from utils.logging_config import get_logger
import numpy as np
import talib
import json
import os
from plugins.plugin import Plugin

logger = get_logger(__name__)


class AnaliseCandles(Plugin):
    PLUGIN_NAME = "analise_candles"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.padroes_talib = self._carregar_padroes_talib()

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "candles": {
                "padroes": {},
                "forca": "FRACA",
                "confianca": 0.0,
            }
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

            klines = dados_completos.get("crus", [])
            if not isinstance(klines, list) or len(klines) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            resultado = self.analisar_padroes(klines, symbol, timeframe)
            if isinstance(dados_completos, dict):
                dados_completos["candles"] = resultado
            return True
        except Exception as e:
            logger.error(f"Erro ao executar analise_candles: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _carregar_padroes_talib(self):
        try:
            caminho = os.path.join("utils", "padroes_talib.json")
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("padroes_talib", []))
        except Exception as e:
            logger.error(f"Erro ao carregar padrões TA-Lib: {e}")
            return set()

    def analisar_padroes(self, dados, symbol, timeframe):
        try:
            logger.debug(f"Analisando padrões para {symbol} - {timeframe}")
            ohlcv = self._extrair_dados(dados, [1, 2, 3, 4, 5])
            open_, high, low, close, volume = (
                ohlcv[1],
                ohlcv[2],
                ohlcv[3],
                ohlcv[4],
                ohlcv[5],
            )

            padroes_detectados = {}
            for func in talib.get_function_groups().get("Pattern Recognition", []):
                nome_padrao = func.lower().replace("cdl", "")
                if nome_padrao not in self.padroes_talib:
                    continue

                resultado = getattr(talib, func)(open_, high, low, close)
                if len(resultado) < 2:
                    continue

                for i in [-2, -1]:  # Verifica candle anterior e atual
                    if resultado[i] == 0:
                        continue
                    direcao = "alta" if resultado[i] > 0 else "baixa"
                    estado = "formado" if i == -2 else "em formação"
                    timestamp = dados[i][0]

                    padroes_detectados[nome_padrao] = {
                        "estado": estado,
                        "sinal": "compra" if direcao == "alta" else "venda",
                        "stop_loss": self._calcular_stop_loss(low, high, direcao),
                        "take_profit": self._calcular_take_profit(close, direcao),
                        "timestamp": timestamp,
                    }

                    logger.info(
                        f"Padrão {nome_padrao} detectado ({estado}) em {symbol}-{timeframe}"
                    )
                    break  # Evita sobrescrever com candle mais recente

            return {
                "padroes": padroes_detectados,
                "forca": self._calcular_forca(close, volume),
                "confianca": self._calcular_confianca(close, volume),
            }
        except Exception as e:
            logger.error(f"Erro na análise de padrões: {e}")
            return {
                "padroes": {},
                "forca": "FRACA",
                "confianca": 0.0,
            }

    def _calcular_stop_loss(self, low, high, direcao):
        try:
            volatilidade = np.std(high[-10:] - low[-10:])
            if direcao == "alta":
                return round(low[-2] - (volatilidade * 1.5), 2)
            else:
                return round(high[-2] + (volatilidade * 1.5), 2)
        except Exception as e:
            logger.error(f"Erro no cálculo de stop loss: {e}")
            return None

    def _calcular_take_profit(self, close, direcao):
        try:
            volatilidade = np.std(close[-10:])
            if direcao == "alta":
                return round(close[-2] + (volatilidade * 2), 2)
            else:
                return round(close[-2] - (volatilidade * 2), 2)
        except Exception as e:
            logger.error(f"Erro no cálculo de take profit: {e}")
            return None

    def _calcular_forca(self, close, volume):
        try:
            variacao = abs(close[-1] - close[-2]) / close[-2]
            vol_rel = volume[-1] / np.mean(volume[-10:]) if len(volume) >= 10 else 1
            pontuacao = variacao * vol_rel
            return (
                "FORTE" if pontuacao > 0.5 else "MÉDIA" if pontuacao > 0.2 else "FRACA"
            )
        except Exception as e:
            logger.error(f"Erro ao calcular força: {e}")
            return "FRACA"

    def _calcular_confianca(self, close, volume):
        try:
            if len(close) < 10 or len(volume) < 10 or np.mean(volume[-10:]) == 0:
                return 0.0
            volatilidade = np.std(close[-10:]) / np.mean(close[-10:])
            vol_rel = volume[-1] / np.mean(volume[-10:])
            confianca = min(max(volatilidade * vol_rel * 100, 0.0), 100.0)
            return round(confianca, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.0

    def _extrair_dados(self, dados, indices):
        try:
            return {
                i: np.array([float(d[i]) for d in dados], dtype=np.float64)
                for i in indices
            }
        except Exception as e:
            logger.error(f"Erro na extração de dados: {e}")
            return {i: np.array([]) for i in indices}
