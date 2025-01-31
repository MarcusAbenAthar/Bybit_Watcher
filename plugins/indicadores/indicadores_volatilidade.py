import psycopg2
from trading_core import Core
from loguru import logger
import talib
from plugins.plugin import Plugin


class IndicadoresVolatilidade(Plugin):
    """
    Plugin para calcular indicadores de volatilidade.
    """

    def __init__(self, core):  # Recebe o Core como argumento
        self.core = core
        self.config = core.config  # Acessa as configurações através do Core

    def calcular_bandas_de_bollinger(self, dados, periodo=20, desvio_padrao=2):
        """
        Calcula as Bandas de Bollinger para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período da média móvel.
            desvio_padrao (float): Número de desvios padrão para calcular as bandas.

        Returns:
            tuple: Uma tupla com as listas da banda superior, da banda média e da banda inferior.
        """
        fechamentos = [candle[4] for candle in dados]
        banda_media = talib.SMA(fechamentos, timeperiod=periodo)
        desvio_padrao = talib.STDDEV(fechamentos, timeperiod=periodo)
        banda_superior = banda_media + desvio_padrao * desvio_padrao
        banda_inferior = banda_media - desvio_padrao * desvio_padrao
        return banda_superior, banda_media, banda_inferior

    def calcular_atr(self, dados, periodo=14):
        """
        Calcula o Average True Range (ATR) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do ATR.

        Returns:
            list: Lista com os valores do ATR.
        """
        # Extrai os valores de high, low e close dos candles
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]

        # Calcula o ATR usando a função ATR do TA-Lib
        atr = talib.ATR(high, low, close, timeperiod=periodo)

        return atr

    def gerar_sinal(self, dados, indicador, tipo, par, timeframe):
        """
        Gera um sinal de compra ou venda com base no indicador de volatilidade fornecido.

        Args:
            dados (list): Lista de candles.
            indicador (str): Nome do indicador de volatilidade ("bandas_de_bollinger" ou "atr").
            tipo (str): Tipo de sinal (depende do indicador).
            par (str): Par de moedas.
            timeframe (str): Timeframe dos candles.

        Returns:
            dict: Um dicionário com o sinal, o stop loss e o take profit.
        """
        try:
            sinal = None
            stop_loss = None
            take_profit = None

            # Obtém o módulo de cálculo de alavancagem do Core
            calculo_alavancagem = (
                self.core.calculo_alavancagem
            )  # Obtém o módulo do Core

            # Calcula a alavancagem ideal (Regra de Ouro: Dinamismo)
            alavancagem = calculo_alavancagem.calcular_alavancagem(
                dados[-1], par, timeframe
            )

            if indicador == "bandas_de_bollinger":
                upper, middle, lower = self.calcular_bandas_de_bollinger(dados)
                if tipo == "rompimento_superior" and dados[-1][4] > upper[-1]:
                    sinal = "compra"
                    stop_loss = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                        0.1 / alavancagem
                    )
                    take_profit = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                        2 / alavancagem
                    )
                elif tipo == "rompimento_inferior" and dados[-1][4] < lower[-1]:
                    sinal = "venda"
                    stop_loss = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                        0.1 / alavancagem
                    )
                    take_profit = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                        2 / alavancagem
                    )

            elif indicador == "atr":
                atr = self.calcular_atr(dados)
                # Lógica para gerar sinais com base no ATR (exemplo: rompimento do ATR)
                if tipo == "rompimento_alta" and dados[-1][4] > dados[-2][4] + atr[-1]:
                    sinal = "compra"
                    stop_loss = dados[-1][3] - atr[-1] * (0.5 / alavancagem)
                    take_profit = dados[-1][2] + atr[-1] * (1.5 / alavancagem)
                elif (
                    tipo == "rompimento_baixa" and dados[-1][4] < dados[-2][4] - atr[-1]
                ):
                    sinal = "venda"
                    stop_loss = dados[-1][2] + atr[-1] * (0.5 / alavancagem)
                    take_profit = dados[-1][3] - atr[-1] * (1.5 / alavancagem)

            return {
                "sinal": sinal,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

        except Exception as e:
            logger.error(f"Erro ao gerar sinal para {indicador} - {tipo}: {e}")
        return {
            "sinal": None,
            "stop_loss": None,
            "take_profit": None,
        }

    def executar(self, dados, par, timeframe):
        """
        Executa o cálculo dos indicadores de volatilidade, gera sinais de trading e salva os resultados no banco de dados.

        Args:
            dados (list): Lista de candles.
            par (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
        """

        try:
            conn = self.core.banco_dados.conexao  # Usa a conexão do Core
            cursor = conn.cursor()

            for candle in dados:
                # Calcula os indicadores de volatilidade para o candle atual
                bandas_superior, bandas_media, bandas_inferior = (
                    self.calcular_bandas_de_bollinger([candle])
                )
                atr = self.calcular_atr([candle])

                # Gera os sinais de compra e venda para o candle atual
                sinal_bandas_rompimento_superior = self.gerar_sinal(
                    [candle],
                    "bandas_de_bollinger",
                    "rompimento_superior",
                    par,
                    timeframe,
                )
                sinal_bandas_rompimento_inferior = self.gerar_sinal(
                    [candle],
                    "bandas_de_bollinger",
                    "rompimento_inferior",
                    par,
                    timeframe,
                )
                sinal_atr_rompimento_alta = self.gerar_sinal(
                    [candle], "atr", "rompimento_alta", par, timeframe
                )
                sinal_atr_rompimento_baixa = self.gerar_sinal(
                    [candle], "atr", "rompimento_baixa", par, timeframe
                )

                # Salva os resultados no banco de dados para o candle atual
                timestamp = int(candle[0] / 1000)  # Converte o timestamp para segundos
                cursor.execute(
                    """
                    INSERT INTO indicadores_volatilidade (
                        par, timeframe, timestamp, bandas_superior, bandas_media, bandas_inferior, atr,
                        sinal_bandas_rompimento_superior, stop_loss_bandas_rompimento_superior, take_profit_bandas_rompimento_superior,
                        sinal_bandas_rompimento_inferior, stop_loss_bandas_rompimento_inferior, take_profit_bandas_rompimento_inferior,
                        sinal_atr_rompimento_alta, stop_loss_atr_rompimento_alta, take_profit_atr_rompimento_alta,
                        sinal_atr_rompimento_baixa, stop_loss_atr_rompimento_baixa, take_profit_atr_rompimento_baixa
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (par, timeframe, timestamp) DO UPDATE
                    SET bandas_superior = EXCLUDED.bandas_superior, bandas_media = EXCLUDED.bandas_media, bandas_inferior = EXCLUDED.bandas_inferior, atr = EXCLUDED.atr,
                        sinal_bandas_rompimento_superior = EXCLUDED.sinal_bandas_rompimento_superior, stop_loss_bandas_rompimento_superior = EXCLUDED.stop_loss_bandas_rompimento_superior, take_profit_bandas_rompimento_superior = EXCLUDED.take_profit_bandas_rompimento_superior,
                        sinal_bandas_rompimento_inferior = EXCLUDED.sinal_bandas_rompimento_inferior, stop_loss_bandas_rompimento_inferior = EXCLUDED.stop_loss_bandas_rompimento_inferior, take_profit_bandas_rompimento_inferior = EXCLUDED.take_profit_bandas_rompimento_inferior,
                        sinal_atr_rompimento_alta = EXCLUDED.sinal_atr_rompimento_alta, stop_loss_atr_rompimento_alta = EXCLUDED.stop_loss_atr_rompimento_alta, take_profit_atr_rompimento_alta = EXCLUDED.take_profit_atr_rompimento_alta,
                        sinal_atr_rompimento_baixa = EXCLUDED.sinal_atr_rompimento_baixa, stop_loss_atr_rompimento_baixa = EXCLUDED.stop_loss_atr_rompimento_baixa, take_profit_atr_rompimento_baixa = EXCLUDED.take_profit_atr_rompimento_baixa;
                    """,
                    (
                        par,
                        timeframe,
                        timestamp,
                        bandas_superior[-1],
                        bandas_media[-1],
                        bandas_inferior[-1],
                        atr[-1],
                        sinal_bandas_rompimento_superior["sinal"],
                        sinal_bandas_rompimento_superior["stop_loss"],
                        sinal_bandas_rompimento_superior["take_profit"],
                        sinal_bandas_rompimento_inferior["sinal"],
                        sinal_bandas_rompimento_inferior["stop_loss"],
                        sinal_bandas_rompimento_inferior["take_profit"],
                        sinal_atr_rompimento_alta["sinal"],
                        sinal_atr_rompimento_alta["stop_loss"],
                        sinal_atr_rompimento_alta["take_profit"],
                        sinal_atr_rompimento_baixa["sinal"],
                        sinal_atr_rompimento_baixa["stop_loss"],
                        sinal_atr_rompimento_baixa["take_profit"],
                    ),
                )

            conn.commit()
            logger.debug(
                f"Indicadores de volatilidade calculados e sinais gerados para {par} - {timeframe}."
            )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular indicadores de volatilidade: {error}")
