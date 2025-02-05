import psycopg2
from plugins.gerente_plugin import obter_calculo_alavancagem, obter_banco_dados
from loguru import logger
import talib
from plugins.plugin import Plugin


class IndicadoresVolatilidade(Plugin):
    """
    Plugin para calcular indicadores de volatilidade.
    """

    def __init__(self):
        """Inicializa o plugin IndicadoresVolatilidade."""
        super().__init__()
        # Obtém o plugin de cálculo de alavancagem
        self.calculo_alavancagem = obter_calculo_alavancagem()
        # Obtém o plugin de banco de dados
        self.banco_dados = obter_banco_dados()

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

    def gerar_sinal(self, dados, indicador, tipo, symbol, timeframe, config):
        """
        Gera um sinal de compra ou venda com base no indicador de volatilidade fornecido.

        Args:
            dados (list): Lista de candles.
            indicador (str): Nome do indicador de volatilidade ("bandas_de_bollinger" ou "atr").
            tipo (str): Tipo de sinal (depende do indicador).
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
            config (ConfigParser): Objeto com as configurações do bot.

        Returns:
            dict: Um dicionário com o sinal, o stop loss e o take profit.
        """
        try:
            sinal = None
            stop_loss = None
            take_profit = None

            # Calcula a alavancagem ideal (Regra de Ouro: Dinamismo)
            alavancagem = self.calculo_alavancagem.calcular_alavancagem(
                dados[-1], symbol, timeframe, config
            )

            if indicador == "bandas_de_bollinger":
                upper, middle, lower = self.calcular_bandas_de_bollinger(dados)
                if tipo == "rompimento_superior" and dados[-1] > upper[-1]:
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.1 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        2 / alavancagem
                    )
                elif tipo == "rompimento_inferior" and dados[-1] < lower[-1]:
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.1 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        2 / alavancagem
                    )

            elif indicador == "atr":
                atr = self.calcular_atr(dados)
                # Lógica para gerar sinais com base no ATR (exemplo: rompimento do ATR)
                if tipo == "rompimento_alta" and dados[-1] > dados[-2] + atr[-1]:
                    sinal = "compra"
                    stop_loss = dados[-1] - atr[-1] * (0.5 / alavancagem)
                    take_profit = dados[-1] + atr[-1] * (1.5 / alavancagem)
                elif tipo == "rompimento_baixa" and dados[-1] < dados[-2] - atr[-1]:
                    sinal = "venda"
                    stop_loss = dados[-1] + atr[-1] * (0.5 / alavancagem)
                    take_profit = dados[-1] - atr[-1] * (1.5 / alavancagem)

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

    def executar(self, dados, symbol, timeframe, config):
        """
        Executa o cálculo dos indicadores de volatilidade, gera sinais de trading e salva os resultados no banco de dados.

        Args:
            dados (list): Lista de candles.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
            config (ConfigParser): Objeto com as configurações do bot.
        """

        try:
            conn = obter_banco_dados().conn
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
                    symbol,
                    timeframe,
                    config,
                )
                sinal_bandas_rompimento_inferior = self.gerar_sinal(
                    [candle],
                    "bandas_de_bollinger",
                    "rompimento_inferior",
                    symbol,
                    timeframe,
                    config,
                )
                sinal_atr_rompimento_alta = self.gerar_sinal(
                    [candle], "atr", "rompimento_alta", symbol, timeframe, config
                )
                sinal_atr_rompimento_baixa = self.gerar_sinal(
                    [candle], "atr", "rompimento_baixa", symbol, timeframe, config
                )

                # Salva os resultados no banco de dados para o candle atual
                timestamp = int(candle / 1000)  # Converte o timestamp para segundos
                cursor.execute(
                    """
                    INSERT INTO indicadores_volatilidade (
                        symbol, timeframe, timestamp, bandas_superior, bandas_media, bandas_inferior, atr,
                        sinal_bandas_rompimento_superior, stop_loss_bandas_rompimento_superior, take_profit_bandas_rompimento_superior,
                        sinal_bandas_rompimento_inferior, stop_loss_bandas_rompimento_inferior, take_profit_bandas_rompimento_inferior,
                        sinal_atr_rompimento_alta, stop_loss_atr_rompimento_alta, take_profit_atr_rompimento_alta,
                        sinal_atr_rompimento_baixa, stop_loss_atr_rompimento_baixa, take_profit_atr_rompimento_baixa
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
                    SET bandas_superior = EXCLUDED.bandas_superior, bandas_media = EXCLUDED.bandas_media, bandas_inferior = EXCLUDED.bandas_inferior, atr = EXCLUDED.atr,
                        sinal_bandas_rompimento_superior = EXCLUDED.sinal_bandas_rompimento_superior, stop_loss_bandas_rompimento_superior = EXCLUDED.stop_loss_bandas_rompimento_superior, take_profit_bandas_rompimento_superior = EXCLUDED.take_profit_bandas_rompimento_superior,
                        sinal_bandas_rompimento_inferior = EXCLUDED.sinal_bandas_rompimento_inferior, stop_loss_bandas_rompimento_inferior = EXCLUDED.stop_loss_bandas_rompimento_inferior, take_profit_bandas_rompimento_inferior = EXCLUDED.take_profit_bandas_rompimento_inferior,
                        sinal_atr_rompimento_alta = EXCLUDED.sinal_atr_rompimento_alta, stop_loss_atr_rompimento_alta = EXCLUDED.stop_loss_atr_rompimento_alta, take_profit_atr_rompimento_alta = EXCLUDED.take_profit_atr_rompimento_alta,
                        sinal_atr_rompimento_baixa = EXCLUDED.sinal_atr_rompimento_baixa, stop_loss_atr_rompimento_baixa = EXCLUDED.stop_loss_atr_rompimento_baixa, take_profit_atr_rompimento_baixa = EXCLUDED.take_profit_atr_rompimento_baixa;
                    """,
                    (
                        symbol,
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
                f"Indicadores de volatilidade calculados e sinais gerados para {symbol} - {timeframe}."
            )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular indicadores de volatilidade: {error}")
