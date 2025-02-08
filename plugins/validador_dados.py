from plugins.plugin import Plugin
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ValidadorDados(Plugin):
    "Plugin para validação de dados OHLCV."

    def __init__(self):
        super().__init__()
        self.nome = "Validador de Dados"
        self.descricao = "Validação robusta de dados OHLCV"
        self.min_candles = 20  # Mínimo de candles para análise

    def validar_estrutura(self, dados):
        "Valida estrutura básica dos dados."
        try:
            if not isinstance(dados, (list, tuple)):
                logger.error("Dados não estão em formato de lista")
                return False

            if len(dados) < self.min_candles:
                logger.error(f"Quantidade insuficiente de candles: {len(dados)}")
                return False

            return True

        except Exception as e:
            logger.error(f"Erro na validação de estrutura: {e}")
            return False

    def validar_candle(self, candle):
        """ "
        Valida valores de um único candle.

        Args:
            candle (list): Lista com dados [timestamp, open, high, low, close, volume]
                timestamp: Unix timestamp em milissegundos
                open: Preço de abertura
                high: Preço máximo
                low: Preço mínimo
                close: Preço de fechamento
                volume: Volume negociado

        Returns:
            bool: True se candle válido, False caso contrário

        Example:
            >>> candle = [1625097600000, 35000.0, 35100.0, 34900.0, 35050.0, 10.5]
            >>> validador.validar_candle(candle)
            True
        """
        try:
            # Log detalhado para debug
            logger.debug(f"Validando candle: {candle}")

            # Valida formato básico
            if not isinstance(candle, (list, tuple)):
                logger.error(
                    f"Candle deve ser lista ou tupla, recebido: {type(candle)}"
                )
                return False

            if len(candle) < 6:
                logger.error(
                    f"Candle deve ter pelo menos 6 elementos, recebido: {len(candle)}"
                )
                return False

            # Verifica se não é um symbol ou timeframe
            if isinstance(candle[0], str) and any(
                candle[0].endswith(suffix)
                for suffix in ["USDT", "1m", "3m", "5m", "15m", "30m", "1h"]
            ):
                logger.error(f"Dados inválidos recebidos como candle: {candle[0]}")
                return False

            # Tenta converter valores para validação
            try:
                dados = {
                    "timestamp": float(candle[0]),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }
            except (ValueError, IndexError) as e:
                logger.error(f"Erro na conversão de valores do candle: {e}")
                logger.debug(f"Valores tentando converter: {candle}")
                return False

            # Validações lógicas de preços
            if not (
                dados["low"] <= dados["open"] <= dados["high"]
                and dados["low"] <= dados["close"] <= dados["high"]
            ):
                logger.error(
                    f"Preços OHLC inválidos: O:{dados['open']} H:{dados['high']} "
                    f"L:{dados['low']} C:{dados['close']}"
                )
                return False

            # Validação de volume
            if dados["volume"] < 0:
                logger.error(f"Volume negativo: {dados['volume']}")
                return False

            # Validação de valores numéricos
            valores = [v for k, v in dados.items() if k != "timestamp"]
            if any(np.isnan(x) or np.isinf(x) for x in valores):
                logger.error("Valores NaN ou Inf detectados")
                return False

            logger.debug("Candle validado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro na validação do candle: {e}")
            return False

    def validar_timeframe(self, timeframe):
        "Valida timeframe."
        timeframes_validos = [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "12h",
            "1d",
        ]
        if timeframe not in timeframes_validos:
            logger.error(f"Timeframe inválido: {timeframe}")
            return False
        return True

    def validar_symbol(self, symbol):
        """
        Valida symbol.

        Args:
            symbol (str): Símbolo a ser validado

        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            # Validação básica
            if not isinstance(symbol, str):
                logger.error(f"Symbol deve ser string, recebido: {type(symbol)}")
                return False

            # Validação de comprimento
            if len(symbol) < 5:  # Mínimo: BTC/USDT
                logger.error(f"Symbol muito curto: {symbol}")
                return False

            # Validação de formato
            if not symbol.endswith(("USDT", "USD", "BTC")):
                logger.error(f"Symbol com formato inválido: {symbol}")
                return False

            return True

        except Exception as e:
            logger.error(f"Erro na validação do symbol: {e}")
            return False

    def validar_dados_completos(self, dados, symbol, timeframe):
        """
        Valida conjunto completo de dados.

        Args:
            dados (list): Lista de candles
            symbol (str): Símbolo do par
            timeframe (str): Timeframe dos dados

        Returns:
            bool: True se todos os dados são válidos
        """
        try:
            # Valida parâmetros básicos
            if not self.validar_symbol(symbol):
                return False

            if not self.validar_timeframe(timeframe):
                return False

            if not self.validar_estrutura(dados):
                return False

            # Valida cada candle
            candles_validos = [
                candle for candle in dados if self.validar_candle(candle)
            ]

            # Verifica quantidade mínima após validação
            if len(candles_validos) < self.min_candles:
                logger.error(
                    f"Quantidade insuficiente de candles válidos: "
                    f"{len(candles_validos)} de {len(dados)}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Erro na validação completa dos dados: {e}")
            return False
