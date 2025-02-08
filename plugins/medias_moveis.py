import logging

logger = logging.getLogger(__name__)
from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_calculo_alavancagem
import talib
import numpy as np


class MediasMoveis(Plugin):
    """Plugin para calcular as médias móveis."""

    def __init__(self, config=None):
        """Inicializa o plugin MediasMoveis."""
        super().__init__()
        self.nome = "Médias Móveis"
        self.config = config
        self.descricao = "Plugin para análise de médias móveis"
        self.alavancagem = 1  # Default value
        # Obtém o plugin de cálculo de alavancagem
        self.calculo_alavancagem = obter_calculo_alavancagem()

    def calcular_media_movel(self, dados, periodo, tipo="simples"):
        """
        Calcula a média móvel para os dados fornecidos.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período da média móvel.
            tipo (str): Tipo da média móvel ("simples", "exponencial", "ponderada").

        Returns:
            list: Lista com os valores da média móvel.
        """
        # Extrai os valores de fechamento dos candles
        fechamentos = [candle for candle in dados]

        if tipo == "simples":
            return talib.SMA(fechamentos, timeperiod=periodo)
        elif tipo == "exponencial":
            return talib.EMA(fechamentos, timeperiod=periodo)
        elif tipo == "ponderada":
            return talib.WMA(fechamentos, timeperiod=periodo)
        else:
            raise ValueError("Tipo de média móvel inválido.")

    def gerar_sinal(self, dados, medias_moveis, symbol, timeframe, config):
        """
        Gera um sinal de compra ou venda com base nos cruzamentos de médias móveis.

        Args:
            dados (list): Lista de candles.
            medias_moveis (list): Lista de médias móveis.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.

        Returns:
            dict: Um dicionário com o sinal, o stop loss e o take profit.
        """
        sinal = None
        stop_loss = None
        take_profit = None

        media_movel_curta = medias_moveis[0]
        media_movel_longa = medias_moveis[1]

        # Verifica se houve cruzamento das médias móveis
        if (
            media_movel_curta[-2] < media_movel_longa[-2]
            and media_movel_curta[-1] > media_movel_longa[-1]
        ):
            sinal = "compra"
        elif (
            media_movel_curta[-2] > media_movel_longa[-2]
            and media_movel_curta[-1] < media_movel_longa[-1]
        ):
            sinal = "venda"

            # Calcula a alavancagem ideal (Regra de Ouro: Dinamismo)
            alavancagem = self.calculo_alavancagem.calcular_alavancagem(
                dados[-1], symbol, timeframe, config
            )

        # Calcula o stop loss e o take profit, considerando a alavancagem
        if sinal == "compra":
            stop_loss = (
                dados[-1][3] - (0.05 / alavancagem) * dados[-1][0]
            )  # Stop loss 5% abaixo do mínimo do último candle
            take_profit = (
                dados[-1][2] + (0.15 / alavancagem) * dados[-1][0]
            )  # Take profit 15% acima do máximo do último candle
        elif sinal == "venda":
            stop_loss = (
                dados[-1][2] + (0.05 / alavancagem) * dados[-1][0]
            )  # Stop loss 5% acima do máximo do último candle
            take_profit = (
                dados[-1][3] - (0.15 / alavancagem) * dados[-1][0]
            )  # Take profit 15% abaixo do mínimo do último candle

        return {
            "sinal": sinal,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }

    def executar(self, dados, symbol, timeframe):
        """
        Executa a análise de médias móveis.

        Args:
            dados (list): Lista de candles
            symbol (str): Símbolo do par
            timeframe (str): Timeframe

        Returns:
            dict: Resultados da análise
        """
        try:
            # Inicializa alavancagem com valor padrão
            self.alavancagem = 1  # Valor default

            if not dados or len(dados) < 20:  # Mínimo de candles para análise
                logger.warning("Dados insuficientes para análise")
                return None

            # Calcular médias móveis
            closes = np.array([float(candle[4]) for candle in dados])
            ma20 = talib.SMA(closes, timeperiod=20)
            ma50 = talib.SMA(closes, timeperiod=50)

            # Calcular alavancagem baseada na volatilidade
            self.alavancagem = self._calcular_alavancagem(closes)

            # Gerar sinal
            sinal = {
                "symbol": symbol,
                "timeframe": timeframe,
                "ma20": ma20[-1],
                "ma50": ma50[-1],
                "alavancagem": self.alavancagem,
                "direcao": "compra" if ma20[-1] > ma50[-1] else "venda",
            }

            return sinal

        except Exception as e:
            logger.error(f"Erro ao processar médias móveis: {e}")
            raise

    def _calcular_alavancagem(self, closes):
        """
        Calcula a alavancagem baseada na volatilidade.
        """
        try:
            volatilidade = np.std(closes[-20:]) / np.mean(closes[-20:])
            alavancagem = max(1, min(20, int(1 / volatilidade)))
            return alavancagem
        except Exception as e:
            logger.error(f"Erro ao calcular alavancagem: {e}")
            return 1  # Valor default seguro
