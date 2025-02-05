from plugins.gerente_plugin import obter_calculo_alavancagem, obter_banco_dados
from loguru import logger
import psycopg2
import talib
from plugins.plugin import Plugin


class IndicadoresTendencia(Plugin):
    """
    Plugin para calcular indicadores de tendência.
    """

    def __init__(self):
        """Inicializa o plugin Indicadores de Tendencia."""
        super().__init__()
        # Obtém o plugin de cálculo de alavancagem
        self.calculo_alavancagem = obter_calculo_alavancagem()
        # Obtém o plugin de banco de dados
        self.banco_dados = obter_banco_dados()

    def calcular_tema(self, dados, periodo=30):
        """
        Calcula a Média Móvel Exponencial Tripla (TEMA) para os dados fornecidos,
        usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período da TEMA.

        Returns:
            list: Lista com os valores da TEMA.
        """
        fechamentos = [candle[4] for candle in dados]
        return talib.TEMA(fechamentos, timeperiod=periodo)

    def calcular_kama(self, dados, periodo=30):
        """
        Calcula a Média Móvel Adaptativa (KAMA) para os dados fornecidos,
        usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período da KAMA.

        Returns:
            list: Lista com os valores da KAMA.
        """
        fechamentos = [candle[4] for candle in dados]
        return talib.KAMA(fechamentos, timeperiod=periodo)

    def calcular_macd_histograma(
        self, dados, fastperiod=12, slowperiod=26, signalperiod=9
    ):
        """
        Calcula o MACD com histograma para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            fastperiod (int): Período da média móvel rápida.
            slowperiod (int): Período da média móvel lenta.
            signalperiod (int): Período da média móvel do sinal.

        Returns:
            tuple: Uma tupla com as listas do MACD, do sinal e do histograma.
        """
        fechamentos = [candle[4] for candle in dados]
        macd, signal, hist = talib.MACD(
            fechamentos,
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod,
        )
        return macd, signal, hist

    def calcular_adx(self, dados, periodo=14):
        """
        Calcula o ADX (Average Directional Index) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do ADX.

        Returns:
            list: Lista com os valores do ADX.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        return talib.ADX(high, low, close, timeperiod=periodo)

    def calcular_aroon(self, dados, periodo=14):
        """
        Calcula o Aroon para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do Aroon.

        Returns:
            tuple: Uma tupla com as listas do Aroon Up e do Aroon Down.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        return talib.AROON(high, low, timeperiod=periodo)

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
        fechamentos = [candle[4] for candle in dados]

        # Calcula o RSI usando a função RSI do TA-Lib
        rsi = talib.RSI(fechamentos, timeperiod=periodo)

        return rsi

    def calcular_macd(
        self, dados, symbol, timeframe, fastperiod=12, slowperiod=26, signalperiod=9
    ):
        """
        Calcula o MACD (Moving Average Convergence Divergence) para os dados fornecidos,
        usando a biblioteca TA-Lib. Ajusta os períodos das médias móveis dinamicamente
        com base no timeframe e na volatilidade do ativo, seguindo as Regras de Ouro.

        Args:
            dados (list): Lista de candles.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
            fastperiod (int): Período base da média móvel rápida.
            slowperiod (int): Período base da média móvel lenta.
            signalperiod (int): Período base da média móvel do sinal.

        Returns:
            tuple: Uma tupla com as listas do MACD, do sinal e do histograma.
        """
        # Ajusta os períodos das médias móveis com base no timeframe
        if timeframe == "1m":
            fastperiod = max(
                7, fastperiod // 2
            )  # Reduz o período para timeframes menores
            slowperiod = max(14, slowperiod // 2)
            signalperiod = max(4, signalperiod // 2)
        elif timeframe == "1d":
            fastperiod = min(
                28, fastperiod * 2
            )  # Aumenta o período para timeframes maiores
            slowperiod = min(52, slowperiod * 2)
            signalperiod = min(18, signalperiod * 2)

        # Calcula a volatilidade do ativo
        volatilidade = self.calcular_volatilidade(dados)

        # Ajusta os períodos das médias móveis com base na volatilidade
        # Aumenta os períodos para volatilidade alta, diminui para volatilidade baixa
        ajuste_volatilidade = int(
            volatilidade * 5
        )  # Ajuste o fator 5 conforme necessário
        fastperiod = max(7, min(28, fastperiod + ajuste_volatilidade))
        slowperiod = max(14, min(52, slowperiod + ajuste_volatilidade))
        signalperiod = max(4, min(18, signalperiod + ajuste_volatilidade))

        # Extrai os valores de fechamento dos candles
        fechamentos = [candle[4] for candle in dados]

        # Calcula o MACD usando a função MACD do TA-Lib
        macd, signal, hist = talib.MACD(
            fechamentos,
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod,
        )

        return macd, signal, hist

    def calcular_adx(self, dados, periodo=14):
        """
        Calcula o ADX (Average Directional Index) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do ADX.

        Returns:
            list: Lista com os valores do ADX.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        return talib.ADX(high, low, close, timeperiod=periodo)

    def calcular_aroon(self, dados, periodo=14):
        """
        Calcula o Aroon para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do Aroon.

        Returns:
            tuple: Uma tupla com as listas do Aroon Up e do Aroon Down.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        return talib.AROON(high, low, timeperiod=periodo)

    def calcular_sar_parabolico(self, dados, acceleration=0.02, maximum=0.2):
        """
        Calcula o SAR Parabólico (Parabolic SAR) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            acceleration (float): Fator de aceleração.
            maximum (float): Valor máximo do fator de aceleração.

        Returns:
            list: Lista com os valores do SAR Parabólico.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        return talib.SAR(high, low, acceleration=acceleration, maximum=maximum)

    def gerar_sinal(self, dados, indicador, tipo, symbol, timeframe, config):
        """
        Gera um sinal de compra ou venda com base no indicador de tendência fornecido,
        seguindo as Regras de Ouro.

        Args:
            dados (list): Lista de candles.
            indicador (str): Nome do indicador de tendência.
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
                elif tipo == "sobrevenda" and rsi[-1] < 30:
                    sinal = "compra"

            # ----- Lógica para o MACD -----
            elif indicador == "macd":
                macd, signal, hist = self.calcular_macd(dados, symbol, timeframe)
                if tipo == "cruzamento_acima" and macd[-1] > signal[-1]:
                    sinal = "compra"
                elif tipo == "cruzamento_abaixo" and macd[-1] < signal[-1]:
                    sinal = "venda"
            # ----- Lógica para o ADX -----
            elif indicador == "adx":
                adx = self.calcular_adx(dados)
                if tipo == "forte_alta" and adx[-1] > 25:
                    sinal = "compra"
                elif tipo == "forte_baixa" and adx[-1] > 25:
                    sinal = "venda"

            # ----- Lógica para o Aroon -----
            elif indicador == "aroon":
                aroon_up, aroon_down = self.calcular_aroon(dados)
                if tipo == "cruzamento_acima" and aroon_up[-1] > aroon_down[-1]:
                    sinal = "compra"
                elif tipo == "cruzamento_abaixo" and aroon_up[-1] < aroon_down[-1]:
                    sinal = "venda"

            # ----- Lógica para o SAR Parabólico -----
            elif indicador == "sar_parabolico":
                sar = self.calcular_sar_parabolico(dados)
                if tipo == "reversao_alta" and sar[-1] < dados[-1][4]:
                    sinal = "compra"
                elif tipo == "reversao_baixa" and sar[-1] > dados[-1][4]:
                    sinal = "venda"

            # ----- Lógica para o TEMA -----
            elif indicador == "tema":
                tema = self.calcular_tema(dados)
                if tipo == "cruzamento_acima" and dados[-1][4] > tema[-1]:
                    sinal = "compra"
                elif tipo == "cruzamento_abaixo" and dados[-1][4] < tema[-1]:
                    sinal = "venda"

            # ----- Lógica para o KAMA -----
            elif indicador == "kama":
                kama = self.calcular_kama(dados)
                if tipo == "cruzamento_acima" and dados[-1][4] > kama[-1]:
                    sinal = "compra"
                elif tipo == "cruzamento_abaixo" and dados[-1][4] < kama[-1]:
                    sinal = "venda"

            # ----- Lógica para o MACD com histograma -----
            elif indicador == "macd_histograma":
                macd, signal, hist = self.calcular_macd_histograma(dados)
                if tipo == "cruzamento_acima" and hist[-1] > 0 and hist[-2] < 0:
                    sinal = "compra"
                elif tipo == "cruzamento_abaixo" and hist[-1] < 0 and hist[-2] > 0:
                    sinal = "venda"

            # Calcula o stop loss e o take profit, considerando a alavancagem
            if sinal == "compra":
                stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (0.1 / alavancagem)
                take_profit = dados[-1] + (dados[-1] - dados[-1]) * (2 / alavancagem)
            elif sinal == "venda":
                stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (0.1 / alavancagem)
                take_profit = dados[-1] - (dados[-1] - dados[-1]) * (2 / alavancagem)

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
        Executa o cálculo dos indicadores de tendência, gera sinais de trading e salva os resultados no banco de dados.

        Args:
            dados (list): Lista de candles.
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
        """
        try:
            conn = obter_banco_dados().conn
            cursor = conn.cursor()

            for candle in dados:
                # Calcula os indicadores de tendência para o candle atual
                rsi = self.calcular_rsi([candle], symbol, timeframe)
                macd, macd_signal, macd_hist = self.calcular_macd(
                    [candle], symbol, timeframe
                )
                adx = self.calcular_adx([candle])
                aroon_up, aroon_down = self.calcular_aroon([candle])
                sar = self.calcular_sar_parabolico([candle])
                tema = self.calcular_tema([candle])
                kama = self.calcular_kama([candle])
                macd_histograma = self.calcular_macd_histograma([candle])

                # Gera os sinais de compra e venda para o candle atual
                sinal_rsi_sobrecompra = self.gerar_sinal(
                    [candle], "rsi", "sobrecompra", symbol, timeframe, config
                )

                sinal_rsi_sobrevenda = self.gerar_sinal(
                    [candle], "rsi", "sobrevenda", symbol, timeframe
                )
                sinal_macd_cruzamento_acima = self.gerar_sinal(
                    [candle], "macd", "cruzamento_acima", symbol, timeframe
                )
                sinal_macd_cruzamento_abaixo = self.gerar_sinal(
                    [candle], "macd", "cruzamento_abaixo", symbol, timeframe
                )
                sinal_adx_forte_alta = self.gerar_sinal(
                    [candle], "adx", "forte_alta", symbol, timeframe
                )
                sinal_adx_forte_baixa = self.gerar_sinal(
                    [candle], "adx", "forte_baixa", symbol, timeframe
                )
                sinal_aroon_cruzamento_acima = self.gerar_sinal(
                    [candle], "aroon", "cruzamento_acima", symbol, timeframe
                )
                sinal_aroon_cruzamento_abaixo = self.gerar_sinal(
                    [candle], "aroon", "cruzamento_abaixo", symbol, timeframe
                )
                sinal_sar_reversao_alta = self.gerar_sinal(
                    [candle], "sar_parabolico", "reversao_alta", symbol, timeframe
                )
                sinal_sar_reversao_baixa = self.gerar_sinal(
                    [candle], "sar_parabolico", "reversao_baixa", symbol, timeframe
                )
                sinal_tema_cruzamento_acima = self.gerar_sinal(
                    [candle], "tema", "cruzamento_acima", symbol, timeframe
                )
                sinal_tema_cruzamento_abaixo = self.gerar_sinal(
                    [candle], "tema", "cruzamento_abaixo", symbol, timeframe
                )
                sinal_kama_cruzamento_acima = self.gerar_sinal(
                    [candle], "kama", "cruzamento_acima", symbol, timeframe
                )
                sinal_kama_cruzamento_abaixo = self.gerar_sinal(
                    [candle], "kama", "cruzamento_abaixo", symbol, timeframe
                )
                sinal_macd_histograma_cruzamento_acima = self.gerar_sinal(
                    [candle], "macd_histograma", "cruzamento_acima", symbol, timeframe
                )
                sinal_macd_histograma_cruzamento_abaixo = self.gerar_sinal(
                    [candle], "macd_histograma", "cruzamento_abaixo", symbol, timeframe
                )

                # Salva os resultados no banco de dados para o candle atual
                timestamp = int(candle / 1000)  # Converte o timestamp para segundos
                cursor.execute(
                    """
                    INSERT INTO indicadores_tendencia (
                        symbol, timeframe, timestamp, rsi, macd, macd_signal, macd_hist, adx, aroon_up, aroon_down, sar, tema, kama, macd_histograma,
                        sinal_rsi_sobrecompra, stop_loss_rsi_sobrecompra, take_profit_rsi_sobrecompra,
                        sinal_rsi_sobrevenda, stop_loss_rsi_sobrevenda, take_profit_rsi_sobrevenda,
                        sinal_macd_cruzamento_acima, stop_loss_macd_cruzamento_acima, take_profit_macd_cruzamento_acima,
                        sinal_macd_cruzamento_abaixo, stop_loss_macd_cruzamento_abaixo, take_profit_macd_cruzamento_abaixo,
                        sinal_adx_forte_alta, stop_loss_adx_forte_alta, take_profit_adx_forte_alta,
                        sinal_adx_forte_baixa, stop_loss_adx_forte_baixa, take_profit_adx_forte_baixa,
                        sinal_aroon_cruzamento_acima, stop_loss_aroon_cruzamento_acima, take_profit_aroon_cruzamento_acima,
                        sinal_aroon_cruzamento_abaixo, stop_loss_aroon_cruzamento_abaixo, take_profit_aroon_cruzamento_abaixo,
                        sinal_sar_reversao_alta, stop_loss_sar_reversao_alta, take_profit_sar_reversao_alta,
                        sinal_sar_reversao_baixa, stop_loss_sar_reversao_baixa, take_profit_sar_reversao_baixa,
                        sinal_tema_cruzamento_acima, stop_loss_tema_cruzamento_acima, take_profit_tema_cruzamento_acima,
                        sinal_tema_cruzamento_abaixo, stop_loss_tema_cruzamento_abaixo, take_profit_tema_cruzamento_abaixo,
                        sinal_kama_cruzamento_acima, stop_loss_kama_cruzamento_acima, take_profit_kama_cruzamento_acima,
                        sinal_kama_cruzamento_abaixo, stop_loss_kama_cruzamento_abaixo, take_profit_kama_cruzamento_abaixo,
                        sinal_macd_histograma_cruzamento_acima, stop_loss_macd_histograma_cruzamento_acima, take_profit_macd_histograma_cruzamento_acima,
                        sinal_macd_histograma_cruzamento_abaixo, stop_loss_macd_histograma_cruzamento_abaixo, take_profit_macd_histograma_cruzamento_abaixo
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE SET
                    rsi = EXCLUDED.rsi,
                    macd = EXCLUDED.macd,
                    macd_signal = EXCLUDED.macd_signal,
                    macd_hist = EXCLUDED.macd_hist,
                    adx = EXCLUDED.adx,
                    aroon_up = EXCLUDED.aroon_up,
                    aroon_down = EXCLUDED.aroon_down,
                    sar = EXCLUDED.sar,
                    tema = EXCLUDED.tema,
                    kama = EXCLUDED.kama,
                    macd_histograma = EXCLUDED.macd_histograma,
                    sinal_rsi_sobrecompra = EXCLUDED.sinal_rsi_sobrecompra,
                    stop_loss_rsi_sobrecompra = EXCLUDED.stop_loss_rsi_sobrecompra,
                    take_profit_rsi_sobrecompra = EXCLUDED.take_profit_rsi_sobrecompra,
                    sinal_rsi_sobrevenda = EXCLUDED.sinal_rsi_sobrevenda,
                    stop_loss_rsi_sobrevenda = EXCLUDED.stop_loss_rsi_sobrevenda,
                    take_profit_rsi_sobrevenda = EXCLUDED.take_profit_rsi_sobrevenda,
                    sinal_macd_cruzamento_acima = EXCLUDED.sinal_macd_cruzamento_acima,
                    stop_loss_macd_cruzamento_acima = EXCLUDED.stop_loss_macd_cruzamento_acima,
                    take_profit_macd_cruzamento_acima = EXCLUDED.take_profit_macd_cruzamento_acima,
                    sinal_macd_cruzamento_abaixo = EXCLUDED.sinal_macd_cruzamento_abaixo,
                    stop_loss_macd_cruzamento_abaixo = EXCLUDED.stop_loss_macd_cruzamento_abaixo,
                    take_profit_macd_cruzamento_abaixo = EXCLUDED.take_profit_macd_cruzamento_abaixo,
                    sinal_adx_forte_alta = EXCLUDED.sinal_adx_forte_alta,
                    stop_loss_adx_forte_alta = EXCLUDED.stop_loss_adx_forte_alta,
                    take_profit_adx_forte_alta = EXCLUDED.take_profit_adx_forte_alta,
                    sinal_adx_forte_baixa = EXCLUDED.sinal_adx_forte_baixa,
                    stop_loss_adx_forte_baixa = EXCLUDED.stop_loss_adx_forte_baixa,
                    take_profit_adx_forte_baixa = EXCLUDED.take_profit_adx_forte_baixa,
                    sinal_aroon_cruzamento_acima = EXCLUDED.sinal_aroon_cruzamento_acima,
                    stop_loss_aroon_cruzamento_acima = EXCLUDED.stop_loss_aroon_cruzamento_acima,
                    take_profit_aroon_cruzamento_acima = EXCLUDED.take_profit_aroon_cruzamento_acima,
                    sinal_aroon_cruzamento_abaixo = EXCLUDED.sinal_aroon_cruzamento_abaixo,
                    stop_loss_aroon_cruzamento_abaixo = EXCLUDED.stop_loss_aroon_cruzamento_abaixo,
                    take_profit_aroon_cruzamento_abaixo = EXCLUDED.take_profit_aroon_cruzamento_abaixo,
                    sinal_sar_reversao_alta = EXCLUDED.sinal_sar_reversao_alta,
                    stop_loss_sar_reversao_alta = EXCLUDED.stop_loss_sar_reversao_alta,
                    take_profit_sar_reversao_alta = EXCLUDED.take_profit_sar_reversao_alta,
                    sinal_sar_reversao_baixa = EXCLUDED.sinal_sar_reversao_baixa,
                    stop_loss_sar_reversao_baixa = EXCLUDED.stop_loss_sar_reversao_baixa,
                    take_profit_sar_reversao_baixa = EXCLUDED.take_profit_sar_reversao_baixa,
                    sinal_tema_cruzamento_acima = EXCLUDED.sinal_tema_cruzamento_acima,
                    stop_loss_tema_cruzamento_acima = EXCLUDED.stop_loss_tema_cruzamento_acima,
                    take_profit_tema_cruzamento_acima = EXCLUDED.take_profit_tema_cruzamento_acima,
                    sinal_tema_cruzamento_abaixo = EXCLUDED.sinal_tema_cruzamento_abaixo,
                    stop_loss_tema_cruzamento_abaixo = EXCLUDED.stop_loss_tema_cruzamento_abaixo,
                    take_profit_tema_cruzamento_abaixo = EXCLUDED.take_profit_tema_cruzamento_abaixo,
                    sinal_kama_cruzamento_acima = EXCLUDED.sinal_kama_cruzamento_acima,
                    stop_loss_kama_cruzamento_acima = EXCLUDED.stop_loss_kama_cruzamento_acima,
                    take_profit_kama_cruzamento_acima = EXCLUDED.take_profit_kama_cruzamento_acima,
                    sinal_kama_cruzamento_abaixo = EXCLUDED.sinal_kama_cruzamento_abaixo,
                    stop_loss_kama_cruzamento_abaixo = EXCLUDED.stop_loss_kama_cruzamento_abaixo,
                    take_profit_kama_cruzamento_abaixo = EXCLUDED.take_profit_kama_cruzamento_abaixo,
                    sinal_macd_histograma_cruzamento_acima = EXCLUDED.sinal_macd_histograma_cruzamento_acima,
                    stop_loss_macd_histograma_cruzamento_acima = EXCLUDED.stop_loss_macd_histograma_cruzamento_acima,
                    take_profit_macd_histograma_cruzamento_acima = EXCLUDED.take_profit_macd_histograma_cruzamento_acima,
                    sinal_macd_histograma_cruzamento_abaixo = EXCLUDED.sinal_macd_histograma_cruzamento_abaixo,
                    stop_loss_macd_histograma_cruzamento_abaixo = EXCLUDED.stop_loss_macd_histograma_cruzamento_abaixo,
                    take_profit_macd_histograma_cruzamento_abaixo = EXCLUDED.take_profit_macd_histograma_cruzamento_abaixo
                )""",
                    (
                        symbol,
                        timeframe,
                        timestamp,
                        rsi[-1],
                        macd[-1],
                        macd_signal[-1],
                        macd_hist[-1],
                        adx[-1],
                        aroon_up[-1],
                        aroon_down[-1],
                        sar[-1],
                        tema[-1],
                        kama[-1],
                        macd_histograma[-1],
                        sinal_rsi_sobrecompra["sinal"],
                        sinal_rsi_sobrecompra["stop_loss"],
                        sinal_rsi_sobrecompra["take_profit"],
                        sinal_rsi_sobrevenda["sinal"],
                        sinal_rsi_sobrevenda["stop_loss"],
                        sinal_rsi_sobrevenda["take_profit"],
                        sinal_macd_cruzamento_acima["sinal"],
                        sinal_macd_cruzamento_acima["stop_loss"],
                        sinal_macd_cruzamento_acima["take_profit"],
                        sinal_macd_cruzamento_abaixo["sinal"],
                        sinal_macd_cruzamento_abaixo["stop_loss"],
                        sinal_macd_cruzamento_abaixo["take_profit"],
                        sinal_adx_forte_alta["sinal"],
                        sinal_adx_forte_alta["stop_loss"],
                        sinal_adx_forte_alta["take_profit"],
                        sinal_adx_forte_baixa["sinal"],
                        sinal_adx_forte_baixa["stop_loss"],
                        sinal_adx_forte_baixa["take_profit"],
                        sinal_aroon_cruzamento_acima["sinal"],
                        sinal_aroon_cruzamento_acima["stop_loss"],
                        sinal_aroon_cruzamento_acima["take_profit"],
                        sinal_aroon_cruzamento_abaixo["sinal"],
                        sinal_aroon_cruzamento_abaixo["stop_loss"],
                        sinal_aroon_cruzamento_abaixo["take_profit"],
                        sinal_sar_reversao_alta["sinal"],
                        sinal_sar_reversao_alta["stop_loss"],
                        sinal_sar_reversao_alta["take_profit"],
                        sinal_sar_reversao_baixa["sinal"],
                        sinal_sar_reversao_baixa["stop_loss"],
                        sinal_sar_reversao_baixa["take_profit"],
                        sinal_tema_cruzamento_acima["sinal"],
                        sinal_tema_cruzamento_acima["stop_loss"],
                        sinal_tema_cruzamento_acima["take_profit"],
                        sinal_tema_cruzamento_abaixo["sinal"],
                        sinal_tema_cruzamento_abaixo["stop_loss"],
                        sinal_tema_cruzamento_abaixo["take_profit"],
                        sinal_kama_cruzamento_acima["sinal"],
                        sinal_kama_cruzamento_acima["stop_loss"],
                        sinal_kama_cruzamento_acima["take_profit"],
                        sinal_kama_cruzamento_abaixo["sinal"],
                        sinal_kama_cruzamento_abaixo["stop_loss"],
                        sinal_kama_cruzamento_abaixo["take_profit"],
                        sinal_macd_histograma_cruzamento_acima["sinal"],
                        sinal_macd_histograma_cruzamento_acima["stop_loss"],
                        sinal_macd_histograma_cruzamento_acima["take_profit"],
                        sinal_macd_histograma_cruzamento_abaixo["sinal"],
                        sinal_macd_histograma_cruzamento_abaixo["stop_loss"],
                        sinal_macd_histograma_cruzamento_abaixo["take_profit"],
                    ),
                )

            conn.commit()
            logger.debug(
                f"Indicadores de tendência calculados e sinais gerados para {symbol} - {timeframe}."
            )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular indicadores de tendência: {error}")
