from utils.logging_config import get_logger

logger = get_logger(__name__)
import numpy as np
from plugins.validador_dados import ValidadorDados
import talib

from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin


class CalculoAlavancagem(Plugin):
    """Plugin para cálculos de alavancagem."""

    def __init__(self):
        """Inicializa o plugin CalculoAlavancagem."""
        super().__init__()
        self.nome = "Cálculo de Alavancagem"
        self.descricao = "Plugin para cálculos de alavancagem"
        self._config = None
        self.cache_volatilidade = {}  # Adicionado cache
        self.gerente = GerentePlugin()

    def inicializar(self, config):
        """Inicializa as dependências do plugin."""
        if not self._config:  # Só inicializa uma vez
            super().inicializar(config)
            self._config = config
            self._validador = ValidadorDados()
            logger.info(f"Plugin {self.nome} inicializado com sucesso")

    def set_gerente(self, gerente):
        self.gerente = gerente

    def obter_exchange(self):
        """Obtém instância da exchange."""
        try:
            conexao = self.gerente.plugins.get(
                "conexao"
            )  # Acessa o dicionário 'plugins'
            if conexao:
                return conexao.exchange
            return None
        except Exception as e:
            logger.error(f"Erro ao obter exchange: {e}")
            return None

    def executar(self, dados, symbol, timeframe):
        """Executa cálculo de alavancagem."""
        try:
            if not self._validador.validar_dados_completos(dados, symbol, timeframe):
                logger.error("Dados inválidos, pulando cálculo de alavancagem")
                return False

            alavancagem = self.calcular_alavancagem(
                dados, symbol, timeframe, self._config
            )
            logger.info(
                f"Alavancagem calculada para {symbol} ({timeframe}): {alavancagem}"
            )

            # Salva a alavancagem no banco de dados
            try:
                self.banco_dados.salvar_alavancagem(symbol, timeframe, alavancagem)
            except Exception as e:
                logger.error(f"Erro ao salvar alavancagem no banco de dados: {e}")

            return True

        except Exception as e:
            logger.error(f"Erro no cálculo de alavancagem: {e}")
            return False

    def calcular_alavancagem(self, dados, symbol, timeframe, config):
        """
        Calcula a alavancagem baseada na volatilidade.

        Args:
            dados: numpy array com dados OHLCV
            symbol: str com o par de trading
            timeframe: str com o timeframe
            config: objeto de configuração

        Returns:
            int: alavancagem calculada
        """
        try:
            chave_cache = f"{symbol}_{timeframe}"
            if chave_cache not in self.cache_volatilidade:
                # Calcula ATR
                atr = self.calcular_atr(dados)
                if atr is None:
                    return 1  # Alavancagem mínima em caso de erro

                # Usa o último valor do ATR
                atr_atual = atr[-1]

                # Calcula volatilidade como percentual do preço
                preco_atual = dados[-1][4]  # Último preço de fechamento
                volatilidade = atr_atual / preco_atual

                # Cache o resultado
                self.cache_volatilidade[chave_cache] = volatilidade
            else:
                volatilidade = self.cache_volatilidade[chave_cache]

            # Obtém alavancagem máxima da config
            alavancagem_maxima = config.getint(
                "trading", "alavancagem_maxima", fallback=20
            )

            # Calcula alavancagem inversa à volatilidade
            alavancagem = int(alavancagem_maxima / (float(volatilidade) * 10))

            # Limita entre 1 e alavancagem_maxima
            return max(1, min(alavancagem, alavancagem_maxima))

        except Exception as e:
            logger.error(f"Erro no cálculo de alavancagem: {e}")
            return 1  # Retorna alavancagem mínima em caso de erro

    def calcular_atr(self, dados):
        """Calcula o ATR (Average True Range)."""
        try:
            dados_np = np.array(dados, dtype=np.float64)  # Força tipo double
            high = dados_np[:, 2]
            low = dados_np[:, 3]
            close = dados_np[:, 4]

            return talib.ATR(high, low, close, timeperiod=14)
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return None
