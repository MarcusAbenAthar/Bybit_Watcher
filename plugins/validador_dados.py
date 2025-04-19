"""
Plugin para validação de dados de entrada (símbolo, timeframe, candles).
"""

from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class ValidadorDados(Plugin):
    PLUGIN_NAME = "validador_dados"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["validação", "dados"]
    PLUGIN_PRIORIDADE = 30

    def __init__(self, conexao=None, **kwargs):
        """
        Inicializa o plugin ValidadorDados.

        Args:
            conexao: Instância do plugin Conexao (opcional, para validar símbolos).
            **kwargs: Outras dependências.
        """
        super().__init__(**kwargs)
        self.min_candles = 20
        self._conexao = conexao
        self._timeframes_padrao = ["1m", "5m", "15m", "1h", "4h", "1d"]

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com configurações.

        Args:
            config: Dicionário com configurações.

        Returns:
            bool: True se inicializado, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            validador_config = config.get("validador", {})
            self.min_candles = validador_config.get("min_candles", self.min_candles)
            if not isinstance(self.min_candles, int) or self.min_candles <= 0:
                logger.error(f"[{self.nome}] min_candles inválido: {self.min_candles}")
                return False

            timeframes = config.get("timeframes", self._timeframes_padrao)
            if not isinstance(timeframes, list) or not timeframes:
                logger.warning(
                    f"[{self.nome}] timeframes inválido. Usando padrão: {self._timeframes_padrao}"
                )
                timeframes = self._timeframes_padrao
            self._timeframes = timeframes

            logger.info(
                f"[{self.nome}] Inicializado com min_candles={self.min_candles}, timeframes={self._timeframes}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Valida dados de entrada e atualiza dados_completos.

        Args:
            dados_completos (dict): Dados com crus.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            resultado_padrao = {"validador_dados": {"status": "INVALIDO"}}

            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                dados_completos["validador_dados"] = resultado_padrao["validador_dados"]
                return True

            if not all([symbol, timeframe]):
                logger.error(
                    f"[{self.nome}] Parâmetros obrigatórios ausentes: symbol={symbol}, timeframe={timeframe}"
                )
                dados_completos["validador_dados"] = resultado_padrao["validador_dados"]
                return True

            if not isinstance(symbol, str):
                logger.error(f"[{self.nome}] symbol não é string: {type(symbol)}")
                dados_completos["validador_dados"] = resultado_padrao["validador_dados"]
                return True
            if not isinstance(timeframe, str):
                logger.error(f"[{self.nome}] timeframe não é string: {type(timeframe)}")
                dados_completos["validador_dados"] = resultado_padrao["validador_dados"]
                return True

            if "crus" not in dados_completos or not isinstance(
                dados_completos["crus"], list
            ):
                logger.error(
                    f"[{self.nome}] crus ausente ou inválido em dados_completos"
                )
                dados_completos["validador_dados"] = resultado_padrao["validador_dados"]
                return True

            crus = dados_completos["crus"]
            status = "VALIDO" if self._validar(crus, symbol, timeframe) else "INVALIDO"
            dados_completos["validador_dados"] = {"status": status}
            logger.info(
                f"[{self.nome}] Dados validados ({status}) para {symbol} - {timeframe}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            dados_completos["validador_dados"] = {"status": "INVALIDO"}
            return True

    def _validar(self, candles: list, symbol: str, timeframe: str) -> bool:
        """
        Valida candles, símbolo e timeframe.

        Args:
            candles: Lista de candles.
            symbol: Símbolo do par.
            timeframe: Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        try:
            if not self._validar_symbol(symbol):
                logger.warning(f"[{self.nome}] Symbol inválido: {symbol}")
                return False
            if not self._validar_timeframe(timeframe):
                logger.warning(f"[{self.nome}] Timeframe inválido: {timeframe}")
                return False
            if not isinstance(candles, list) or len(candles) < self.min_candles:
                logger.warning(
                    f"[{self.nome}] Número insuficiente de candles: {len(candles)} < {self.min_candles}"
                )
                return False
            return all(self._validar_candle(c) for c in candles)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao validar dados: {e}")
            return False

    def _validar_symbol(self, symbol: str) -> bool:
        """
        Valida o símbolo do par.

        Args:
            symbol: Símbolo do par.

        Returns:
            bool: True se válido, False caso contrário.
        """
        try:
            # Configuração de sufixos permitidos
            sufixos = self._config.get("validador", {}).get(
                "symbol_suffixes", ["USDT", "USD", "BTC"]
            )
            if not sufixos:
                logger.warning(
                    f"[{self.nome}] Nenhum sufixo de símbolo configurado. Usando padrão: {sufixos}"
                )

            # Verificação via conexao.py, se disponível
            if self._conexao and hasattr(self._conexao, "exchange"):
                markets = self._conexao.exchange.markets
                if markets and symbol in markets:
                    return True
                logger.warning(
                    f"[{self.nome}] Símbolo {symbol} não encontrado na exchange"
                )
                return False

            # Fallback: validação por sufixo
            return any(symbol.endswith(s) for s in sufixos)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao validar símbolo {symbol}: {e}")
            return False

    def _validar_timeframe(self, tf: str) -> bool:
        """
        Valida o timeframe.

        Args:
            tf: Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        try:
            return tf in self._timeframes
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao validar timeframe {tf}: {e}")
            return False

    def _validar_candle(self, candle) -> bool:
        """
        Valida uma candle individual.

        Args:
            candle: Lista ou tupla com [timestamp, open, high, low, close, volume].

        Returns:
            bool: True se válida, False caso contrário.
        """
        try:
            if not isinstance(candle, (list, tuple)) or len(candle) < 6:
                logger.debug(f"[{self.nome}] Candle com formato inválido: {candle}")
                return False
            ts, o, h, l, c, v = map(float, candle[:6])
            if not (
                l <= o <= h
                and l <= c <= h
                and v >= 0
                and all(np.isfinite(x) for x in [o, h, l, c, v])
            ):
                logger.debug(f"[{self.nome}] Candle com valores inválidos: {candle}")
                return False
            return True
        except Exception as e:
            logger.debug(f"[{self.nome}] Erro ao validar candle: {e}")
            return False
