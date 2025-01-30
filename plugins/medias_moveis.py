from venv import logger
import psycopg2
from core import Core
from plugins.plugin import Plugin
import talib


class MediasMoveis(Plugin):
    """
    Plugin para calcular as médias móveis.
    """

    def __init__(self, container: AppModule):
        self.container = container
        super().__init__(container.config())

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
        if tipo == "simples":
            return talib.SMA(dados, timeperiod=periodo)
        elif tipo == "exponencial":
            return talib.EMA(dados, timeperiod=periodo)
        elif tipo == "ponderada":
            return talib.WMA(dados, timeperiod=periodo)
        else:
            raise ValueError("Tipo de média móvel inválido.")

    def gerar_sinal(self, dados, medias_moveis, par, timeframe):
        """
        Gera um sinal de compra ou venda com base nos cruzamentos de médias móveis.

        Args:
            dados (list): Lista de candles.
            medias_moveis (list): Lista de médias móveis.
            par (str): Par de moedas.
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
            dados, par, timeframe
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


def executar(self, dados, par, timeframe):
    """
    Executa o cálculo das médias móveis, gera sinais de trading e salva os resultados no banco de dados.

    Args:
        dados (list): Lista de candles.
        par (str): Par de moedas.
        timeframe (str): Timeframe dos candles.
    """
    try:
        conn = self.banco_dados.conn
        cursor = conn.cursor()

        # Calcula as médias móveis
        media_movel_curta = self.calcular_media_movel(dados, periodo=20, tipo="simples")
        media_movel_longa = self.calcular_media_movel(dados, periodo=50, tipo="simples")

        # Gera o sinal de compra ou venda
        sinal = self.gerar_sinal(
            dados, [media_movel_curta, media_movel_longa], par, timeframe
        )

        # Salva os dados no banco de dados
        timestamp = int(dados[-1][0] / 1000)  # Converte o timestamp para segundos
        cursor.execute(
            """
            INSERT INTO medias_moveis (par, timeframe, timestamp, sinal, stop_loss, take_profit)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (par, timeframe, timestamp) DO UPDATE
            SET sinal = EXCLUDED.sinal, stop_loss = EXCLUDED.stop_loss, take_profit = EXCLUDED.take_profit;
            """,
            (
                par,
                timeframe,
                timestamp,
                sinal["sinal"],
                sinal["stop_loss"],
                sinal["take_profit"],
            ),
        )

        conn.commit()
        logger.debug(
            f"Médias móveis calculadas e sinais gerados para {par} - {timeframe}."
        )

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Erro ao calcular médias móveis: {error}")
