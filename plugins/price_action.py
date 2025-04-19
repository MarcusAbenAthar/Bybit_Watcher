"""
Plugin de análise de price action com reconhecimento de padrões simples de candle,
baseado em corpo, pavio e direção.
"""

from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class PriceAction(Plugin):
    PLUGIN_NAME = "price_action"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["price_action", "candles", "direcional"]
    PLUGIN_PRIORIDADE = 40

    def __init__(self, **kwargs):
        """
        Inicializa o plugin de price action.
        """
        super().__init__(**kwargs)
        self._min_klines = 20  # Mínimo de k-lines para análise
        self._doji_threshold = 0.1  # Proporção corpo/range para doji

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações (ex.: número mínimo de k-lines).

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            self._min_klines = config.get("price_action", {}).get(
                "min_klines", self._min_klines
            )
            self._doji_threshold = config.get("price_action", {}).get(
                "doji_threshold", self._doji_threshold
            )

            if not (isinstance(self._min_klines, int) and self._min_klines > 0):
                logger.error(f"[{self.nome}] min_klines inválido: {self._min_klines}")
                return False
            if not (
                isinstance(self._doji_threshold, (int, float))
                and 0.0 < self._doji_threshold < 1.0
            ):
                logger.error(
                    f"[{self.nome}] doji_threshold inválido: {self._doji_threshold}"
                )
                return False

            logger.info(
                f"[{self.nome}] inicializado com min_klines={self._min_klines}, "
                f"doji_threshold={self._doji_threshold}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

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

        if len(klines) < self._min_klines:
            logger.error(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines, "
                f"requer {self._min_klines}"
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
                for i in [1, 2, 3, 4, 5]:
                    float(kline[i])
            except (TypeError, ValueError):
                logger.error(
                    f"[{self.nome}] Valor não numérico em k-line para {symbol} - {timeframe}: {kline}"
                )
                return False

        return True

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a análise de price action e armazena resultados.

        Args:
            dados_completos (dict): Dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
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

        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            dados_completos["price_action"] = resultado_padrao["price_action"]
            return True

        if not all([symbol, timeframe]):
            logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
            dados_completos["price_action"] = resultado_padrao["price_action"]
            return True

        klines = dados_completos.get("crus", [])
        if not self._validar_klines(klines, symbol, timeframe):
            dados_completos["price_action"] = resultado_padrao["price_action"]
            return True

        try:
            sinal = self.gerar_sinal(klines)
            dados_completos["price_action"] = sinal
            logger.info(f"[{self.nome}] Concluído para {symbol}-{timeframe}")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            dados_completos["price_action"] = resultado_padrao["price_action"]
            return True

    def gerar_sinal(self, klines: list) -> dict:
        """
        Gera sinal baseado em padrões de price action.

        Args:
            klines: Lista de k-lines.

        Returns:
            dict: Sinal com direção, força, confiança e padrão.
        """
        try:
            dados = self._extrair_dados(klines, [1, 2, 3, 4, 5])
            open_, high, low, close, volume = (
                dados[1],
                dados[2],
                dados[3],
                dados[4],
                dados[5],
            )

            ultimo = {
                "open": open_[-1],
                "high": high[-1],
                "low": low[-1],
                "close": close[-1],
                "volume": volume[-1],
            }

            padrao = self._identificar_padrao(ultimo)
            direcao = self._analisar_direcao(ultimo)
            forca = self._calcular_forca(ultimo, klines)

            vol_rel = (
                volume[-1] / np.mean(volume[-10:]) if np.mean(volume[-10:]) > 0 else 1.0
            )
            confianca = round(min(max(forca * (0.7 + 0.3 * vol_rel), 0.0), 1.0), 2)
            direcao_final = direcao if padrao != "doji" else "LATERAL"
            forca_label = (
                "FORTE"
                if confianca >= 0.7
                else "MÉDIA" if confianca >= 0.3 else "FRACA"
            )

            return {
                "direcao": direcao_final,
                "forca": forca_label,
                "confianca": confianca,
                "padrao": padrao,
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao gerar sinal: {e}", exc_info=True)
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "padrao": None,
            }

    def _identificar_padrao(self, candle: dict) -> str:
        """
        Identifica o padrão do candle (ex.: alta, baixa, doji).

        Args:
            candle: Dicionário com open, high, low, close.

        Returns:
            str: Padrão identificado.
        """
        try:
            corpo = abs(candle["close"] - candle["open"])
            range_ = candle["high"] - candle["low"]
            if range_ == 0:
                return "indefinido"
            proporcao = corpo / range_
            if proporcao < self._doji_threshold:
                return "doji"
            return "alta" if candle["close"] > candle["open"] else "baixa"
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao identificar padrão: {e}")
            return "indefinido"

    def _calcular_forca(self, candle: dict, klines: list) -> float:
        """
        Calcula a força do padrão com base no corpo e volume.

        Args:
            candle: Dicionário com open, high, low, close, volume.
            klines: Lista de k-lines para contexto.

        Returns:
            float: Força do padrão (0.0 a 1.0).
        """
        try:
            corpo = abs(candle["close"] - candle["open"])
            range_ = candle["high"] - candle["low"]
            forca_base = corpo / range_ if range_ > 0 else 0.0

            # Incorporar volume
            dados = self._extrair_dados(klines, [5])
            volume = dados[5]
            vol_rel = (
                volume[-1] / np.mean(volume[-10:]) if np.mean(volume[-10:]) > 0 else 1.0
            )
            return round(min(max(forca_base * (0.7 + 0.3 * vol_rel), 0.0), 1.0), 4)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular força: {e}")
            return 0.0

    def _analisar_direcao(self, candle: dict) -> str:
        """
        Analisa a direção do candle.

        Args:
            candle: Dicionário com open, high, low, close.

        Returns:
            str: Direção (ALTA, BAIXA, LATERAL).
        """
        try:
            if candle["close"] > candle["open"]:
                return "ALTA"
            elif candle["close"] < candle["open"]:
                return "BAIXA"
            return "LATERAL"
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao analisar direção: {e}")
            return "LATERAL"

    def _extrair_dados(self, dados: list, indices: list) -> dict:
        """
        Extrai dados especificados das k-lines.

        Args:
            dados: Lista de k-lines.
            indices: Lista de índices a extrair (ex.: [1, 2, 3, 4]).

        Returns:
            dict: Dicionário com arrays para cada índice.
        """
        try:
            return {
                i: np.array([float(k[i]) for k in dados], dtype=np.float64)
                for i in indices
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na extração dos dados: {e}")
            return {i: np.array([]) for i in indices}
