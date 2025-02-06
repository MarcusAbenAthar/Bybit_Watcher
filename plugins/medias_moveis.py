from loguru import logger
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
        Executa o cálculo das médias móveis, gera sinais de trading e salva os resultados no banco de dados.

        Args:
            dados (list): Lista de candles.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
        """
        try:
            from plugins.gerente_plugin import obter_banco_dados

            banco_dados = obter_banco_dados(self.config)
            # Converter os dados para numpy array e extrair apenas os preços de fechamento
            dados_fechamento = [
                candle[4] for candle in dados
            ]  # índice 4 é o preço de fechamento
            fechamentos = np.array(dados_fechamento, dtype=np.float64)

            # Calcular médias móveis
            ma_curta = talib.SMA(fechamentos, timeperiod=9)
            ma_longa = talib.SMA(fechamentos, timeperiod=21)

            # Gera o sinal de compra ou venda
            sinal = self.gerar_sinal(
                dados,
                [ma_curta, ma_longa],
                symbol,
                timeframe,
                self.config,
            )

            if sinal[
                "sinal"
            ]:  # Verifica se o sinal é válido antes de salvar no banco de dados.
                # Salva os dados no banco de dados
                timestamp = int(
                    dados[-1][0] / 1000
                )  # Converte o timestamp symbola segundos
                banco_dados.inserir_dados(
                    "medias_moveis",
                    {  # Usando a função inserir_dados do Core
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "timestamp": timestamp,
                        "sinal": sinal["sinal"],
                        "stop_loss": sinal["stop_loss"],
                        "take_profit": sinal["take_profit"],
                    },
                )

                logger.debug(
                    f"Médias móveis calculadas e sinais gerados para {symbol} - {timeframe}."
                )
            else:
                logger.debug(f"Nenhum sinal gerado para {symbol} - {timeframe}.")

            return {"ma_curta": ma_curta, "ma_longa": ma_longa}

        except Exception as e:
            logger.error(f"Erro ao processar médias móveis: {e}")
            raise
