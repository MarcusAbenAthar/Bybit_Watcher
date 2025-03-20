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
            # Ajusta min_candles se presente no config como dict
            if (
                config
                and "validador" in config
                and "min_candles" in config["validador"]
            ):
                try:
                    self.min_candles = int(config["validador"]["min_candles"])
                except (ValueError, TypeError):
                    logger.warning(
                        "min_candles no config não é válido, usando padrão 20"
                    )
            self.cache_validacoes = {}
            self.inicializado = True
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar {self.nome}: {e}")
            return False

    def validar_estrutura(self, dados):
        """Valida estrutura básica dos dados."""
        try:
            # Verifica se dados é None
            if dados is None:
                logger.error("Dados são None")
                return False
            # Converte numpy array para lista, se necessário
            if isinstance(dados, np.ndarray):
                dados = dados.tolist()
                logger.debug("Dados convertidos de numpy array para lista")
            # Verifica se é lista ou tupla
            if not isinstance(dados, (list, tuple)):
                logger.error(
                    f"Dados não estão em formato de lista ou tupla, tipo recebido: {type(dados)}"
                )
                return False
            if len(dados) < self.min_candles:
                logger.error(f"Quantidade insuficiente de candles: {len(dados)}")
                return False
            return True
        except Exception as e:
            logger.error(f"Erro na validação de estrutura: {e}")
            return False

    def validar_candle(self, candle):
        """Valida valores de um único candle."""
        try:
            # logger.debug(f"Validando candle: {candle}")
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
            if not (
                dados["low"] <= dados["open"] <= dados["high"]
                and dados["low"] <= dados["close"] <= dados["high"]
            ):
                logger.error(
                    f"Preços OHLC inválidos: O:{dados['open']} H:{dados['high']} L:{dados['low']} C:{dados['close']}"
                )
                return False
            if dados["volume"] < 0:
                logger.error(f"Volume negativo: {dados['volume']}")
                return False
            valores = [v for k, v in dados.items() if k != "timestamp"]
            if any(np.isnan(x) or np.isinf(x) for x in valores):
                logger.error("Valores NaN ou Inf detectados")
                return False
            # logger.debug("Candle validado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro na validação do candle: {e}")
            return False

    def validar_timeframe(self, timeframe):
        """Valida timeframe."""
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
        """Valida symbol."""
        try:
            if not isinstance(symbol, str):
                logger.error(f"Symbol deve ser string, recebido: {type(symbol)}")
                return False
            if len(symbol) < 5:
                logger.error(f"Symbol muito curto: {symbol}")
                return False
            if not symbol.endswith(("USDT", "USD", "BTC")):
                logger.error(f"Symbol com formato inválido: {symbol}")
                return False
            return True
        except Exception as e:
            logger.error(f"Erro na validação do symbol: {e}")
            return False

    def validar_dados_completos(self, dados, symbol, timeframe):
        """Valida conjunto completo de dados."""
        try:
            if not self.validar_symbol(symbol):
                return False
            if not self.validar_timeframe(timeframe):
                return False
            if not self.validar_estrutura(dados):
                return False
            candles_validos = [
                candle for candle in dados if self.validar_candle(candle)
            ]
            if len(candles_validos) < self.min_candles:
                logger.error(
                    f"Quantidade insuficiente de candles válidos: {len(candles_validos)} de {len(dados)}"
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Erro na validação completa dos dados: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not dados_completos or "crus" not in dados_completos:
                logger.error("Estrutura de dados incompleta")
                return False

            dados = dados_completos["crus"]
            if not self.validar_estrutura(dados):
                logger.warning(f"Dados inválidos para {symbol} ({timeframe})")
                return False

            # Passa os dados validados para "processados"
            dados_completos["processados"]["ohlcv"] = dados
            logger.info(f"Dados validados para {symbol} ({timeframe})")
            return True

        except Exception as e:
            logger.error(f"Erro ao executar ValidadorDados: {e}")
            return False

    def validar_dados(self, dados):
        """Valida um conjunto de dados."""
        try:
            if dados is None or len(dados) == 0:
                raise ValueError("Dados vazios ou nulos")
            dados_np = np.array(dados)
            if len(dados_np.shape) != 2 or dados_np.shape[1] != 6:
                raise ValueError("Formato de dados inválido")
            if np.any(np.isnan(dados_np)) or np.any(np.isinf(dados_np)):
                raise ValueError("Dados contêm valores NaN ou Inf")
            return True
        except Exception as e:
            logger.error(f"Erro na validação de dados: {e}")
            raise ValueError(str(e))
