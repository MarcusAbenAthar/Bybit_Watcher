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
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        if not super().inicializar(config):
            return False
        logger.info(
            f"[{self.nome}] inicializado com {len(self._padroes_talib)} padrões TA-Lib"
        )
        return True

    def _validar_klines(self, klines: list, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de klines.

        Args:
            klines: Lista de k-lines.
            symbol: Símbolo do par.
            timeframe: Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(klines, list):
            logger.error(f"[{self.nome}] klines não é uma lista: {type(klines)}")
            return False

        if len(klines) < 20:
            logger.error(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines"
            )
            return False

        for kline in klines:
            if not isinstance(kline, (list, tuple)) or len(kline) < 6:
                logger.error(
                    f"[{self.nome}] K-line malformada para {symbol} - {timeframe}: {kline}"
                )
                return False
            try:
                # Verificar se open, high, low, close, volume são numéricos
                for i in range(1, 6):  # Índices 1 a 5
                    float(kline[i])
            except (TypeError, ValueError):
                logger.error(
                    f"[{self.nome}] Valor não numérico em k-line para {symbol} - {timeframe}: {kline}"
                )
                return False

        return True

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a análise de padrões de candlestick e armazena resultados.

        Args:
            dados_completos (dict): Dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        resultado_padrao = {
            "candles": {"padroes": {}, "forca": "LATERAL", "confianca": 0.0}
        }

        dados_completos = kwargs.get("dados_completos")
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")

        if not all([dados_completos, symbol, timeframe]):
            logger.error(
                f"[{self.nome}] Parâmetros obrigatórios ausentes: symbol={symbol}, timeframe={timeframe}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            dados_completos["candles"] = resultado_padrao["candles"]
            return True

        crus = dados_completos.get("crus", [])
        if not self._validar_klines(crus, symbol, timeframe):
            dados_completos["candles"] = resultado_padrao["candles"]
            return True

        try:
            resultado = self._analisar(crus, symbol, timeframe)
            dados_completos["candles"] = resultado
            logger.debug(
                f"[{self.nome}] Análise concluída para {symbol}-{timeframe}: {resultado}"
            )
            return True

        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao executar análise de candles: {e}", exc_info=True
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _carregar_padroes(self) -> set:
        """
        Carrega os padrões TA-Lib do arquivo JSON.

        Returns:
            set: Conjunto de nomes de padrões TA-Lib.

        Raises:
            RuntimeError: Se o arquivo não for encontrado ou os padrões estiverem vazios.
        """
        caminho = os.path.join("utils", "padroes_talib.json")
        try:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo {caminho} não encontrado.")

            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)

            padroes = set(data.get("padroes_talib", []))
            if not padroes:
                logger.error(f"[{self.nome}] Nenhum padrão TA-Lib carregado do JSON.")
                raise ValueError("Lista de padrões TA-Lib vazia.")
            return padroes

        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao carregar padrões TA-Lib: {e}", exc_info=True
            )
            raise RuntimeError("Falha crítica ao carregar os padrões TA-Lib.")

    def _analisar(self, candles: list, symbol: str, timeframe: str) -> dict:
        """
        Analisa os padrões de candlestick usando TA-Lib.

        Args:
            candles: Lista de k-lines.
            symbol: Símbolo do par.
            timeframe: Timeframe.

        Returns:
            dict: Resultados com padrões, força e confiança.
        """
        logger.debug(
            f"[{self.nome}] Analisando padrões TA-Lib para {symbol}-{timeframe}"
        )
        ohlcv = self._extrair_ohlcv(candles)
        open_, high, low, close, volume = (
            ohlcv["open"],
            ohlcv["high"],
            ohlcv["low"],
            ohlcv["close"],
            ohlcv["volume"],
        )

        if any(len(arr) < 10 for arr in [open_, high, low, close, volume]):
            raise ValueError("OHLCV incompleto ou insuficiente para análise")

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

                try:
                    timestamp = candles[i][0]
                except IndexError:
                    logger.warning(
                        f"[{self.nome}] Timestamp não encontrado para índice {i}"
                    )
                    continue

                sl = self._calcular_sl(low, high, direcao)
                tp = self._calcular_tp(close, direcao)
                if sl is None or tp is None:
                    logger.warning(
                        f"[{self.nome}] Padrão {nome_padrao} ignorado por SL/TP inválido"
                    )
                    continue

                padroes[nome_padrao] = {
                    "estado": "formado" if i == -2 else "em formação",
                    "sinal": sinal,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "timestamp": timestamp,
                }

                logger.info(
                    f"[{self.nome}] Padrão {nome_padrao} ({sinal}) detectado em {symbol}-{timeframe}"
                )
                break  # só pega o mais recente

        forca = self._calcular_forca(close, volume)
        confianca = self._calcular_confianca(close, volume, len(padroes))

        return {
            "padroes": padroes,
            "forca": forca,
            "confianca": confianca,
        }

    def _extrair_ohlcv(self, candles: list) -> dict:
        """
        Extrai OHLCV das k-lines.

        Args:
            candles: Lista de k-lines.

        Returns:
            dict: Arrays de open, high, low, close, volume.
        """
        try:
            return {
                "open": np.array([float(c[1]) for c in candles]),
                "high": np.array([float(c[2]) for c in candles]),
                "low": np.array([float(c[3]) for c in candles]),
                "close": np.array([float(c[4]) for c in candles]),
                "volume": np.array([float(c[5]) for c in candles]),
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair OHLCV: {e}", exc_info=True)
            return {k: np.array([]) for k in ["open", "high", "low", "close", "volume"]}

    def _calcular_sl(self, low, high, direcao):
        """
        Calcula o stop-loss com base na volatilidade.

        Args:
            low, high: Arrays de preços low e high.
            direcao: Direção do padrão (alta ou baixa).

        Returns:
            float: Valor do stop-loss ou None se erro.
        """
        try:
            if len(low) < 10 or len(high) < 10:
                return None
            volatilidade = np.std(high[-10:] - low[-10:])
            return (
                round(low[-2] - volatilidade * 1.5, 2)
                if direcao == "alta"
                else round(high[-2] + volatilidade * 1.5, 2)
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro no SL: {e}")
            return None

    def _calcular_tp(self, close, direcao):
        """
        Calcula o take-profit com base na volatilidade.

        Args:
            close: Array de preços close.
            direcao: Direção do padrão (alta ou baixa).

        Returns:
            float: Valor do take-profit ou None se erro.
        """
        try:
            if len(close) < 10:
                return None
            volatilidade = np.std(close[-10:])
            return (
                round(close[-2] + volatilidade * 2, 2)
                if direcao == "alta"
                else round(close[-2] - volatilidade * 2, 2)
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro no TP: {e}")
            return None

    def _calcular_forca(self, close, volume):
        """
        Calcula a força do padrão com base em variação e volume.

        Args:
            close, volume: Arrays de preços close e volume.

        Returns:
            str: Força do padrão (FORTE, MÉDIA, LATERAL).
        """
        try:
            if len(close) < 2 or len(volume) < 10:
                return "LATERAL"
            variacao = abs(close[-1] - close[-2]) / close[-2]
            vol_rel = volume[-1] / np.mean(volume[-10:])
            score = variacao * vol_rel
            if score > 0.6:
                return "FORTE"
            elif score > 0.25:
                return "MÉDIA"
            else:
                return "LATERAL"
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na força: {e}")
            return "LATERAL"

    def _calcular_confianca(self, close, volume, padroes_detectados):
        """
        Calcula a confiança do padrão com base em volatilidade, volume e número de padrões.

        Args:
            close, volume: Arrays de preços close e volume.
            padroes_detectados: Número de padrões detectados.

        Returns:
            float: Confiança normalizada entre 0.0 e 1.0.
        """
        try:
            if len(close) < 10 or len(volume) < 10:
                return 0.0
            volatilidade = np.std(close[-10:]) / np.mean(close[-10:])
            vol_rel = volume[-1] / np.mean(volume[-10:])
            padrao_bonus = 0.1 * padroes_detectados
            confianca = min(volatilidade * vol_rel + padrao_bonus, 1.0)
            return round(max(0.0, confianca), 2)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na confiança: {e}")
            return 0.0
