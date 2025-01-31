from venv import logger  # Certifique-se de ter o logger configurado corretamente
from trading_core import Core
from plugins.plugin import Plugin
import talib


class CalculoAlavancagem(Plugin):
    """
    Plugin para calcular a alavancagem ideal para cada operação, agora integrado com o Core.
    """

    def __init__(self, core: Core):  # Agora recebe o Core na inicialização
        self.core = core
        super().__init__(
            self.core.config
        )  # Inicializa a classe Plugin com as configurações do Core
        self.conexao = self.core.conexao  # Obtém a conexão com a exchange do Core
        self.cache_volatilidade = {}  # Inicializa o cache de volatilidade

    def calcular_alavancagem(self, data, par, timeframe):
        """
        Calcula a alavancagem ideal para a operação, considerando a volatilidade e as Regras de Ouro.

        Args:
            data (dict): Dicionário com os dados do candle.
            par (str): Par de moedas.
            timeframe (str): Timeframe dos candles.

        Returns:
            int: Alavancagem ideal para a operação.
        """
        # Verifica se a volatilidade já foi calculada para o par e timeframe
        chave_cache = f"{par}-{timeframe}"
        if chave_cache not in self.cache_volatilidade:
            # Obter o histórico de preços do ativo (agora, usando a conexão com a Bybit do Core)
            historico = self.conexao.obter_exchange().fetch_ohlcv(
                par, timeframe, limit=500
            )

            # Calcular a volatilidade do ativo (exemplo com ATR)
            self.cache_volatilidade[chave_cache] = self.calcular_atr(historico)

        # Obter a volatilidade do cache
        volatilidade = self.cache_volatilidade[chave_cache]

        # Definir a alavancagem máxima (Regra de Ouro: Seguro)
        alavancagem_maxima = self.core.config.getint(
            "Geral", "NIVEL_ALAVANCAGEM"
        )  # Obtém do config.ini

        # Calcular a alavancagem ideal com base na volatilidade (Regra de Ouro: Criterioso e Dinamismo)
        # Ajuste o fator 10 conforme necessário para sua estratégia e perfil de risco
        alavancagem = int(alavancagem_maxima / (volatilidade * 10))

        # Garantir que a alavancagem seja pelo menos 1 (Regra de Ouro: Seguro)
        alavancagem = max(1, alavancagem)

        # Log da alavancagem calculada (Regra de Ouro: Clareza)
        logger.debug(f"Alavancagem calculada para {par} - {timeframe}: {alavancagem}")

        return alavancagem

    def calcular_atr(self, historico):
        """
        Calcula o Average True Range (ATR) do histórico de candles usando TA-Lib.

        Args:
            historico (list): Lista de candles.

        Returns:
            float: Valor do ATR.
        """
        # Extrai os valores de high, low e close do histórico
        high = [candle[2] for candle in historico]
        low = [candle[3] for candle in historico]
        close = [candle[4] for candle in historico]

        # Calcula o ATR usando a função ATR do TA-Lib (Regra de Ouro: Eficiente)
        atr = talib.ATR(
            high, low, close, timeperiod=14
        )  # timeperiod é o período do ATR (padrão: 14)

        # Retorna o último valor do ATR
        return atr[-1]
