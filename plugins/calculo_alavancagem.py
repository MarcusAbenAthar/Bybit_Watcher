# calculo_alavancagem.py
# Plugin para cálculos de alavancagem baseados na volatilidade.

from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class CalculoAlavancagem(Plugin):
    """Plugin para cálculos de alavancagem."""

    PLUGIN_NAME = "calculo_alavancagem"
    PLUGIN_TYPE = "analise"

    def __init__(self, config=None):
        """Inicializa o plugin CalculoAlavancagem."""
        super().__init__()
        self.nome = "Cálculo de Alavancagem"
        self.descricao = "Plugin para cálculos de alavancagem"
        self._config = config
        self.cache_volatilidade = {}
        self._validador = None
        self.inicializado = False

    def inicializar(self, config):
        """Inicializa as dependências do plugin."""
        try:
            if self.inicializado:
                return True
            if not super().inicializar(config):
                return False
            self._config = config
            if (
                not hasattr(self, "_validador")
                or not self._validador
                or not self._validador.inicializado
            ):
                logger.error(
                    "Validador de dados não foi injetado ou não está inicializado"
                )
                return False
            self.inicializado = True
            logger.info(f"Plugin {self.nome} inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar plugin {self.nome}: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol", "BTCUSDT")
            timeframe = kwargs.get("timeframe", "1h")

            if not dados_completos or "crus" not in dados_completos:
                logger.error("Dados crus não encontrados em dados_completos")
                return False

            dados_crus = dados_completos["crus"]

            if not self._validador.validar_dados_completos(
                dados_crus, symbol, timeframe
            ):
                logger.warning(f"Dados inválidos para {symbol} ({timeframe})")
                return False

            alavancagem = self.calcular_alavancagem(
                dados_crus, symbol, timeframe, self._config
            )

            dados_completos["processados"]["calculo_alavancagem"] = alavancagem
            return True
        except Exception as e:
            logger.error(f"Erro ao calcular alavancagem: {e}")
            return False

    def calcular_alavancagem(self, dados, symbol, timeframe, config):
        """Calcula a alavancagem baseada na volatilidade."""
        try:
            chave_cache = f"{symbol}_{timeframe}"
            if chave_cache not in self.cache_volatilidade:
                atr = self.calcular_atr(dados)
                if atr is None:
                    return 1
                atr_atual = atr[-1]
                preco_atual = float(dados[-1][4])  # Último preço de fechamento
                volatilidade = atr_atual / preco_atual
                self.cache_volatilidade[chave_cache] = volatilidade
            else:
                volatilidade = self.cache_volatilidade[chave_cache]
            trading_config = config.get("trading", {})
            alavancagem_maxima = int(trading_config.get("alavancagem_maxima", 20))
            alavancagem = int(alavancagem_maxima / (volatilidade * 10))
            resultado = max(1, min(alavancagem, alavancagem_maxima))
            logger.debug(f"Alavancagem calculada: {resultado}")
            return resultado
        except Exception as e:
            logger.error(f"Erro no cálculo de alavancagem: {e}")
            return 1

    def calcular_atr(self, dados):
        """Calcula o ATR (Average True Range)."""
        try:
            if not dados or len(dados) < 14:
                logger.warning(
                    f"Dados insuficientes para calcular ATR: {len(dados)} períodos fornecidos"
                )
                return None
            dados_np = np.array(dados, dtype=np.float64)
            if np.any(np.isnan(dados_np)):
                logger.error("Dados contêm valores NaN")
                return None
            high = dados_np[:, 2]
            low = dados_np[:, 3]
            close = dados_np[:, 4]
            atr = talib.ATR(high, low, close, timeperiod=14)
            logger.debug(f"ATR calculado: {atr[-1]}")
            return atr
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return None
