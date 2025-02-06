from plugins.gerente_plugin import obter_calculo_alavancagem, obter_banco_dados
import logging

logger = logging.getLogger(__name__)
import psycopg2
import talib
from plugins.plugin import Plugin


class IndicadoresOsciladores(Plugin):
    def __init__(self, config=None):
        """Inicializa o plugin IndicadoresOsciladores."""
        super().__init__()
        self.nome = "Indicadores Osciladores"
        self.config = config
        # Acessa a função de cálculo de alavancagem
        self.calculo_alavancagem = obter_calculo_alavancagem()
        # Acesso ao banco de dados
        self.banco_dados = obter_banco_dados(config)

    def calcular_rsi(self, dados, symbol, timeframe, periodo=14):
        """
        Calcula o RSI (Relative Strength Index) para os dados fornecidos, usando a biblioteca TA-Lib.
        Considera diferentes períodos de RSI para diferentes timeframes e ajusta o período dinamicamente
        com base na volatilidade do ativo, seguindo as Regras de Ouro.

        Args:
            dados (list): Lista de candles.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
            periodo (int): Período base do RSI.

        Returns:
            list: Lista com os valores do RSI.
        """
        # Ajusta o período do RSI com base no timeframe
        if timeframe == "1m":
            periodo = max(7, periodo // 2)  # Reduz o período para timeframes menores
        elif timeframe == "1d":
            periodo = min(28, periodo * 2)  # Aumenta o período para timeframes maiores

        # Calcula a volatilidade do ativo
        volatilidade = self.calcular_volatilidade(dados)

        # Ajusta o período do RSI com base na volatilidade
        # Aumenta o período para volatilidade alta, diminui para volatilidade baixa
        ajuste_volatilidade = int(
            volatilidade * 10
        )  # Ajuste o fator 10 conforme necessário
        periodo = max(7, min(28, periodo + ajuste_volatilidade))

        # Extrai os valores de fechamento dos candles
        fechamentos = [candle for candle in dados]

        # Calcula o RSI usando a função RSI do TA-Lib
        rsi = talib.RSI(fechamentos, timeperiod=periodo)
        logger.debug(f"RSI calculado para {symbol} - {timeframe} - período {periodo}.")
        return rsi

    def calcular_estocastico(
        self,
        dados,
        timeframe,
        fastk_period=5,
        slowk_period=3,
        slowk_matype=0,
        slowd_period=3,
        slowd_matype=0,
    ):
        """
        Calcula o Estocástico para os dados fornecidos, usando a biblioteca TA-Lib.
        Ajusta os períodos do Estocástico dinamicamente com base no timeframe e na
        volatilidade do ativo, seguindo as Regras de Ouro.

        Args:
            dados (list): Lista de candles.
            timeframe (str): Timeframe dos candles.
            fastk_period (int): Período base do Estocástico Lento (%K).
            slowk_period (int): Período da média móvel do %K.
            slowk_matype (int): Tipo da média móvel do %K (0=SMA, 1=EMA, 2=WMA, ...).
            slowd_period (int): Período da média móvel do %D.
            slowd_matype (int): Tipo da média móvel do %D (0=SMA, 1=EMA, 2=WMA, ...).

        Returns:
            tuple: Uma tupla com as listas do Estocástico Lento (%K) e do Estocástico Rápido (%D).
        """
        # Ajusta os períodos do Estocástico com base no timeframe
        if timeframe == "1m":
            fastk_period = max(
                3, fastk_period // 2
            )  # Reduz o período para timeframes menores
            slowk_period = max(2, slowk_period // 2)
            slowd_period = max(2, slowd_period // 2)
        elif timeframe == "1d":
            fastk_period = min(
                10, fastk_period * 2
            )  # Aumenta o período para timeframes maiores
            slowk_period = min(6, slowk_period * 2)
            slowd_period = min(6, slowd_period * 2)

        # Calcula a volatilidade do ativo
        volatilidade = self.calcular_volatilidade(dados)

        # Ajusta os períodos do Estocástico com base na volatilidade
        # Aumenta os períodos para volatilidade alta, diminui para volatilidade baixa
        ajuste_volatilidade = int(
            volatilidade * 3
        )  # Ajuste o fator 3 conforme necessário
        fastk_period = max(3, min(10, fastk_period + ajuste_volatilidade))
        slowk_period = max(2, min(6, slowk_period + ajuste_volatilidade))
        slowd_period = max(2, min(6, slowd_period + ajuste_volatilidade))

        # Extrai os valores de high, low e close dos candles
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]

        # Calcula o Estocástico usando a função STOCH do TA-Lib
        slowk, slowd = talib.STOCH(
            high,
            low,
            close,
            fastk_period=fastk_period,
            slowk_period=slowk_period,
            slowk_matype=slowk_matype,
            slowd_period=slowd_period,
            slowd_matype=slowd_matype,
        )

        return slowk, slowd

    def calcular_mfi(self, dados, periodo=14):
        """
        Calcula o Índice de Fluxo de Dinheiro (MFI) para os dados fornecidos,
        usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do MFI.

        Returns:
            list: Lista com os valores do MFI.
        """
        # Extrai os valores de high, low, close e volume dos candles
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]

        # Calcula o MFI usando a função MFI do TA-Lib
        mfi = talib.MFI(high, low, close, volume, timeperiod=periodo)

        return mfi

    def gerar_sinal(self, dados, indicador, tipo, symbol, timeframe, config):
        """
        Gera um sinal de compra ou venda com base no indicador oscilador fornecido,
        seguindo as Regras de Ouro, incluindo o Dinamismo.

        Args:
            dados (list): Lista de candles.
            indicador (str): Nome do indicador oscilador ("rsi", "estocastico" ou "mfi").
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

            # ----- Lógica para o RSI -----
            if indicador == "rsi":
                rsi = self.calcular_rsi(dados, symbol, timeframe)
                if tipo == "sobrecompra" and rsi[-1] > 70:
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )
                elif tipo == "sobrevenda" and rsi[-1] < 30:
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )

            # ----- Lógica para o Estocástico -----
            elif indicador == "estocastico":
                slowk, slowd = self.calcular_estocastico(dados, timeframe)
                if tipo == "sobrecompra" and slowk[-1] > 80 and slowd[-1] > 80:
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )
                elif tipo == "sobrevenda" and slowk[-1] < 20 and slowd[-1] < 20:
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )

            # ----- Lógica para o MFI -----
            elif indicador == "mfi":
                mfi = self.calcular_mfi(dados)
                if tipo == "sobrecompra" and mfi[-1] > 80:
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )
                elif tipo == "sobrevenda" and mfi[-1] < 20:
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )

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

    def executar(self, dados, symbol, timeframe):
        """
        Executa o cálculo dos indicadores osciladores, gera sinais de trading e salva os resultados no banco de dados.

        Args:
            dados (list): Lista de candles.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
        """
        try:
            conn = self.banco_dados.conn
            cursor = conn.cursor()

            for candle in dados:
                # Calcula os indicadores de osciladores para o candle atual
                rsi = self.calcular_rsi([candle], symbol, timeframe)
                estocastico_lento, estocastico_rapido = self.calcular_estocastico(
                    [candle], timeframe
                )
                mfi = self.calcular_mfi([candle])

                # Gera os sinais de compra e venda para o candle atual
                sinal_rsi_sobrecompra = self.gerar_sinal(
                    [candle], "rsi", "sobrecompra", symbol, timeframe, self.config
                )
                sinal_rsi_sobrevenda = self.gerar_sinal(
                    [candle], "rsi", "sobrevenda", symbol, timeframe, self.config
                )
                sinal_estocastico_sobrecompra = self.gerar_sinal(
                    [candle],
                    "estocastico",
                    "sobrecompra",
                    symbol,
                    timeframe,
                    self.config,
                )
                sinal_estocastico_sobrevenda = self.gerar_sinal(
                    [candle],
                    "estocastico",
                    "sobrevenda",
                    symbol,
                    timeframe,
                    self.config,
                )
                sinal_mfi_sobrecompra = self.gerar_sinal(
                    [candle], "mfi", "sobrecompra", symbol, timeframe, self.config
                )
                sinal_mfi_sobrevenda = self.gerar_sinal(
                    [candle], "mfi", "sobrevenda", symbol, timeframe, self.config
                )

                # Salva os resultados no banco de dados para o candle atual
                timestamp = int(candle / 1000)  # Converte o timestamp para segundos
                cursor.execute(
                    """
                    INSERT INTO indicadores_osciladores (
                        symbol, timeframe, timestamp, rsi, estocastico_lento, estocastico_rapido, mfi,
                        sinal_rsi_sobrecompra, stop_loss_rsi_sobrecompra, take_profit_rsi_sobrecompra,
                        sinal_rsi_sobrevenda, stop_loss_rsi_sobrevenda, take_profit_rsi_sobrevenda,
                        sinal_estocastico_sobrecompra, stop_loss_estocastico_sobrecompra, take_profit_estocastico_sobrecompra,
                        sinal_estocastico_sobrevenda, stop_loss_estocastico_sobrevenda, take_profit_estocastico_sobrevenda,
                        sinal_mfi_sobrecompra, stop_loss_mfi_sobrecompra, take_profit_mfi_sobrecompra,
                        sinal_mfi_sobrevenda, stop_loss_mfi_sobrevenda, take_profit_mfi_sobrevenda
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
                    SET rsi = EXCLUDED.rsi, estocastico_lento = EXCLUDED.estocastico_lento, estocastico_rapido = EXCLUDED.estocastico_rapido, mfi = EXCLUDED.mfi,
                        sinal_rsi_sobrecompra = EXCLUDED.sinal_rsi_sobrecompra, stop_loss_rsi_sobrecompra = EXCLUDED.stop_loss_rsi_sobrecompra, take_profit_rsi_sobrecompra = EXCLUDED.take_profit_rsi_sobrecompra,
                        sinal_rsi_sobrevenda = EXCLUDED.sinal_rsi_sobrevenda, stop_loss_rsi_sobrevenda = EXCLUDED.stop_loss_rsi_sobrevenda, take_profit_rsi_sobrevenda = EXCLUDED.take_profit_rsi_sobrevenda,
                        sinal_estocastico_sobrecompra = EXCLUDED.sinal_estocastico_sobrecompra, stop_loss_estocastico_sobrecompra = EXCLUDED.stop_loss_estocastico_sobrecompra, take_profit_estocastico_sobrecompra = EXCLUDED.take_profit_estocastico_sobrecompra,
                        sinal_estocastico_sobrevenda = EXCLUDED.sinal_estocastico_sobrevenda, stop_loss_estocastico_sobrevenda = EXCLUDED.stop_loss_estocastico_sobrevenda, take_profit_estocastico_sobrevenda = EXCLUDED.take_profit_estocastico_sobrevenda,
                        sinal_mfi_sobrecompra = EXCLUDED.sinal_mfi_sobrecompra, stop_loss_mfi_sobrecompra = EXCLUDED.stop_loss_mfi_sobrecompra, take_profit_mfi_sobrecompra = EXCLUDED.take_profit_mfi_sobrecompra,
                        sinal_mfi_sobrevenda = EXCLUDED.sinal_mfi_sobrevenda, stop_loss_mfi_sobrevenda = EXCLUDED.stop_loss_mfi_sobrevenda, take_profit_mfi_sobrevenda = EXCLUDED.take_profit_mfi_sobrevenda;
                    """,
                    (
                        symbol,
                        timeframe,
                        timestamp,
                        rsi[-1],
                        estocastico_lento[-1],
                        estocastico_rapido[-1],
                        mfi[-1],
                        sinal_rsi_sobrecompra["sinal"],
                        sinal_rsi_sobrecompra["stop_loss"],
                        sinal_rsi_sobrecompra["take_profit"],
                        sinal_rsi_sobrevenda["sinal"],
                        sinal_rsi_sobrevenda["stop_loss"],
                        sinal_rsi_sobrevenda["take_profit"],
                        sinal_estocastico_sobrecompra["sinal"],
                        sinal_estocastico_sobrecompra["stop_loss"],
                        sinal_estocastico_sobrecompra["take_profit"],
                        sinal_estocastico_sobrevenda["sinal"],
                        sinal_estocastico_sobrevenda["stop_loss"],
                        sinal_estocastico_sobrevenda["take_profit"],
                        sinal_mfi_sobrecompra["sinal"],
                        sinal_mfi_sobrecompra["stop_loss"],
                        sinal_mfi_sobrecompra["take_profit"],
                        sinal_mfi_sobrevenda["sinal"],
                        sinal_mfi_sobrevenda["stop_loss"],
                        sinal_mfi_sobrevenda["take_profit"],
                    ),
                )

            conn.commit()
            logger.debug(
                f"Indicadores de osciladores calculados e sinais gerados para {symbol} - {timeframe}."
            )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular indicadores de osciladores: {error}")
