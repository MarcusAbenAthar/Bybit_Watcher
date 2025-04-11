"""Plugin para detecção de padrões de candle com TA-Lib."""

import os
import json
import numpy as np
import talib
from typing import Dict, Any
from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class AnaliseCandles(Plugin):
    PLUGIN_NAME = "analise_candles"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["candles", "padroes", "price_action"]
    PLUGIN_PRIORIDADE = 40

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._padroes_talib = self._carregar_padroes()

    def inicializar(self, config: Dict[str, Any]) -> bool:
        if not super().inicializar(config):
            return False
        logger.info(
            "AnaliseCandles inicializado com %d padrões TA-Lib",
            len(self._padroes_talib),
        )
        return True

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "candles": {"padroes": {}, "forca": "LATERAL", "confianca": 0.0}
        }

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros obrigatórios ausentes")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            crus = dados_completos.get("crus", [])
            if not isinstance(crus, list) or len(crus) < 20:
                logger.warning(f"Dados crus insuficientes para {symbol} - {timeframe}")
                dados_completos["candles"] = resultado_padrao["candles"]
                return True

            resultado = self._analisar(crus, symbol, timeframe)
            dados_completos["candles"] = resultado
            return True

        except Exception as e:
            logger.error(f"Erro no plugin AnaliseCandles: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _carregar_padroes(self) -> set:
        try:
            caminho = os.path.join("utils", "padroes_talib.json")
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("padroes_talib", []))
        except Exception as e:
            logger.error(f"Erro ao carregar padrões TA-Lib: {e}")
            return set()

    def _analisar(self, candles: list, symbol: str, timeframe: str) -> dict:
        try:
            logger.debug(f"Analisando padrões TA-Lib para {symbol}-{timeframe}")
            ohlcv = self._extrair_ohlcv(candles)
            open_, high, low, close, volume = (
                ohlcv["open"],
                ohlcv["high"],
                ohlcv["low"],
                ohlcv["close"],
                ohlcv["volume"],
            )

            padroes = {}
            for func in talib.get_function_groups().get("Pattern Recognition", []):
                nome_padrao = func.lower().replace("cdl", "")
                if nome_padrao not in self._padroes_talib:
                    continue

                resultado = getattr(talib, func)(open_, high, low, close)
                if len(resultado) < 2:
                    continue

                for i in [-2, -1]:
                    if resultado[i] == 0:
                        continue
                    direcao = "alta" if resultado[i] > 0 else "baixa"
                    sinal = "compra" if direcao == "alta" else "venda"
                    timestamp = candles[i][0]

                    padroes[nome_padrao] = {
                        "estado": "formado" if i == -2 else "em formação",
                        "sinal": sinal,
                        "stop_loss": self._calcular_sl(low, high, direcao),
                        "take_profit": self._calcular_tp(close, direcao),
                        "timestamp": timestamp,
                    }
                    logger.info(
                        f"Padrão {nome_padrao} ({sinal}) detectado em {symbol}-{timeframe}"
                    )
                    break

            forca = self._calcular_forca(close, volume)
            confianca = self._calcular_confianca(close, volume, len(padroes))

            return {
                "padroes": padroes,
                "forca": forca,
                "confianca": confianca,
            }

        except Exception as e:
            logger.error(f"Erro ao analisar candles: {e}", exc_info=True)
            return {
                "padroes": {},
                "forca": "LATERAL",
                "confianca": 0.0,
            }

    def _extrair_ohlcv(self, candles: list) -> dict:
        try:
            return {
                "open": np.array([float(c[1]) for c in candles]),
                "high": np.array([float(c[2]) for c in candles]),
                "low": np.array([float(c[3]) for c in candles]),
                "close": np.array([float(c[4]) for c in candles]),
                "volume": np.array([float(c[5]) for c in candles]),
            }
        except Exception as e:
            logger.error(f"Erro ao extrair OHLCV: {e}")
            return {k: np.array([]) for k in ["open", "high", "low", "close", "volume"]}

    def _calcular_sl(self, low, high, direcao):
        try:
            volatilidade = np.std(high[-10:] - low[-10:])
            return (
                round(low[-2] - volatilidade * 1.5, 2)
                if direcao == "alta"
                else round(high[-2] + volatilidade * 1.5, 2)
            )
        except Exception as e:
            logger.error(f"Erro no SL: {e}")
            return None

    def _calcular_tp(self, close, direcao):
        try:
            volatilidade = np.std(close[-10:])
            return (
                round(close[-2] + volatilidade * 2, 2)
                if direcao == "alta"
                else round(close[-2] - volatilidade * 2, 2)
            )
        except Exception as e:
            logger.error(f"Erro no TP: {e}")
            return None

    def _calcular_forca(self, close, volume):
        try:
            variacao = abs(close[-1] - close[-2]) / close[-2]
            vol_rel = volume[-1] / np.mean(volume[-10:]) if len(volume) >= 10 else 1
            score = variacao * vol_rel
            if score > 0.6:
                return "FORTE"
            elif score > 0.25:
                return "MÉDIA"
            else:
                return "LATERAL"
        except Exception as e:
            logger.error(f"Erro na força: {e}")
            return "LATERAL"

    def _calcular_confianca(self, close, volume, padroes_detectados):
        try:
            if len(close) < 10 or len(volume) < 10:
                return 0.0
            volatilidade = np.std(close[-10:]) / np.mean(close[-10:])
            vol_rel = volume[-1] / np.mean(volume[-10:])
            padrao_bonus = 0.1 * padroes_detectados
            confianca = min(volatilidade * vol_rel * 100 + padrao_bonus * 100, 100.0)
            return round(confianca, 2)
        except Exception as e:
            logger.error(f"Erro na confiança: {e}")
            return 0.0
