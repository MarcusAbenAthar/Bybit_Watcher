from utils.logging_config import get_logger
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class ValidadorDados(Plugin):
    """Plugin para validação de dados de trading."""

    # Identificador explícito do plugin
    PLUGIN_NAME = "validador_dados"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o plugin ValidadorDados."""
        super().__init__()
        self.nome = "validador_dados"
        self.descricao = "Plugin para validação de dados de trading"
        self._config = None
        self.cache_validacoes = {}
        self.min_candles = 20  # Mínimo de candles para análise válida
        self.inicializado = False

    def inicializar(self, config):
        """Inicializa o plugin com as configurações fornecidas."""
        try:
            if self.inicializado:
                return True

            if not super().inicializar(config):
                return False

            self._config = config
            self.cache_validacoes = {}
            self.inicializado = True

            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar {self.nome}: {e}")
            return False

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

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a validação dos dados.

        Args:
            *args: Argumentos posicionais ignorados
            **kwargs: Argumentos nomeados contendo:
                dados (dict/list): Dicionário com dados ou lista de candles
                symbol (str): Símbolo do par
                timeframe (str): Timeframe dos dados
                config (dict): Configurações do bot

        Returns:
            bool: True se executado com sucesso
        """
        try:
            # Extrai os parâmetros necessários
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            # Validação dos parâmetros
            if not all([dados, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados["validador_dados"] = {
                        "status": "ERRO",
                        "valido": False,
                        "mensagem": "Parâmetros necessários não fornecidos",
                    }
                return True

            # Inicializa o resultado da validação
            resultado_validacao = {
                "status": "ERRO",
                "valido": False,
                "mensagem": "Dados inválidos",
            }

            # Executa validação completa
            if isinstance(dados, dict):
                # Se dados é um dicionário, valida a estrutura geral
                resultado_validacao["valido"] = True
                resultado_validacao["status"] = "OK"
                resultado_validacao["mensagem"] = "Dados válidos"
            else:
                # Se dados é uma lista, valida como candles
                valido = self.validar_dados_completos(dados, symbol, timeframe)
                resultado_validacao["valido"] = valido
                resultado_validacao["status"] = "OK" if valido else "ERRO"
                resultado_validacao["mensagem"] = (
                    "Dados válidos" if valido else "Dados inválidos"
                )

            # Atualiza o dicionário de dados com o resultado
            if isinstance(dados, dict):
                dados["validador_dados"] = resultado_validacao

            return True

        except Exception as e:
            logger.error(f"Erro ao validar dados: {e}")
            if isinstance(dados, dict):
                dados["validador_dados"] = {
                    "status": "ERRO",
                    "valido": False,
                    "mensagem": str(e),
                }
            return True

    def validar_dados(self, dados):
        """
        Valida um conjunto de dados.

        Args:
            dados: numpy.ndarray com os dados a serem validados

        Returns:
            bool: True se os dados são válidos

        Raises:
            ValueError: Se os dados são inválidos
        """
        try:
            if dados is None or len(dados) == 0:
                raise ValueError("Dados vazios ou nulos")

            # Converte para numpy array se não for
            dados_np = np.array(dados)

            # Verifica shape dos dados
            if len(dados_np.shape) != 2 or dados_np.shape[1] != 6:
                raise ValueError("Formato de dados inválido")

            # Verifica valores inválidos
            if np.any(np.isnan(dados_np)) or np.any(np.isinf(dados_np)):
                raise ValueError("Dados contêm valores NaN ou Inf")

            return True

        except Exception as e:
            logger.error(f"Erro na validação de dados: {e}")
            raise ValueError(str(e))
