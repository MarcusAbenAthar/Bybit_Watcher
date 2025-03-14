import psycopg2
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresVolatilidade(Plugin):
    """
    Plugin para calcular indicadores de volatilidade.
    """

    def __init__(self, gerente: GerentePlugin, config=None):
        """
        Inicializa o plugin IndicadoresVolatilidade.

        Args:
            gerente: Instância do gerenciador de plugins
            config: Configurações do sistema
        """
        super().__init__()
        self.nome = "Indicadores de Volatilidade"
        self.config = config
        self.gerente = gerente
        # Acessa o plugin de cálculo de alavancagem através do gerente
        self.calculo_alavancagem = self.gerente.obter_calculo_alavancagem()
        # Obtém o plugin de banco de dados através do gerente
        self.banco_dados = self.gerente.obter_banco_dados()

    def _validar_e_converter_valor(self, valor):
        """
        Valida e converte um valor para float, tratando casos especiais.

        Args:
            valor: Valor a ser convertido

        Returns:
            float: Valor convertido ou None se inválido
        """
        try:
            # Se for None ou vazio, retorna None
            if valor is None or str(valor).strip() == "":
                return None

            # Converte para string e remove caracteres de notação científica
            valor_str = str(valor).replace("e", "").replace("E", "").replace("n", "")

            # Verifica se há um número válido após remoção
            if (
                not valor_str
                or not valor_str.replace(".", "", 1).replace("-", "", 1).isdigit()
            ):
                return None

            return float(valor_str)
        except (ValueError, TypeError):
            return None

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
        try:
            # Valida e extrai valores numéricos
            fechamentos = []

            for candle in dados:
                if len(candle) < 5:
                    continue

                valor = self._validar_e_converter_valor(candle[4])
                if valor is not None:
                    fechamentos.append(valor)

            # Verifica se temos dados suficientes
            if len(fechamentos) < periodo:
                logger.warning(
                    f"Dados insuficientes para calcular Bandas de Bollinger: {len(fechamentos)}/{periodo}"
                )
                return np.array([0]), np.array([0]), np.array([0])

            # Converte para array numpy para compatibilidade com TALib
            fechamentos = np.array(fechamentos, dtype=np.float64)
            banda_media = talib.SMA(fechamentos, timeperiod=periodo)
            std_dev = talib.STDDEV(fechamentos, timeperiod=periodo)
            banda_superior = banda_media + std_dev * desvio_padrao
            banda_inferior = banda_media - std_dev * desvio_padrao

            return banda_superior, banda_media, banda_inferior

        except Exception as e:
            logger.error(f"Erro ao calcular Bandas de Bollinger: {e}")
            return np.array([0]), np.array([0]), np.array([0])

    def calcular_atr(self, dados, periodo=14):
        """
        Calcula o Average True Range (ATR) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do ATR.

        Returns:
            list: Lista com os valores do ATR.
        """
        try:
            # Valida e extrai valores numéricos
            highs = []
            lows = []
            closes = []

            for candle in dados:
                if len(candle) < 5:
                    continue

                high_val = self._validar_e_converter_valor(candle[2])
                low_val = self._validar_e_converter_valor(candle[3])
                close_val = self._validar_e_converter_valor(candle[4])

                if (
                    high_val is not None
                    and low_val is not None
                    and close_val is not None
                ):
                    highs.append(high_val)
                    lows.append(low_val)
                    closes.append(close_val)

            # Verifica se temos dados suficientes
            if len(highs) < periodo or len(lows) < periodo or len(closes) < periodo:
                logger.warning(
                    f"Dados insuficientes para calcular ATR: {len(highs)}/{periodo}"
                )
                return np.array([0])

            # Converte para arrays numpy
            high = np.array(highs, dtype=np.float64)
            low = np.array(lows, dtype=np.float64)
            close = np.array(closes, dtype=np.float64)

            # Calcula o ATR usando a função ATR do TA-Lib
            atr = talib.ATR(high, low, close, timeperiod=periodo)

            return atr

        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return np.array([0])

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

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo dos indicadores de volatilidade.

        Args:
            *args: Argumentos posicionais ignorados
            **kwargs: Argumentos nomeados contendo:
                dados (list): Lista de candles
                symbol (str): Símbolo do par
                timeframe (str): Timeframe da análise
                config (dict): Configurações do bot

        Returns:
            bool: True se executado com sucesso
        """

        try:
            # Extrai os parâmetros necessários
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            # Validação dos parâmetros
            if not all([dados, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                dados["volatilidade"] = {
                    "bandas_bollinger": None,
                    "atr": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            # Verifica se o banco de dados está disponível e inicializado
            if not self.banco_dados:
                logger.warning("Banco de dados não disponível")
                dados["volatilidade"] = {
                    "bandas_bollinger": None,
                    "atr": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            # Verificar se a conexão existe no banco de dados
            if not hasattr(self.banco_dados, "conn") or not self.banco_dados.conn:
                logger.warning("Conexão com banco de dados não disponível")
                return True

            cursor = self.banco_dados.conn.cursor()

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
                    self.config,
                )
                sinal_bandas_rompimento_inferior = self.gerar_sinal(
                    [candle],
                    "bandas_de_bollinger",
                    "rompimento_inferior",
                    symbol,
                    timeframe,
                    self.config,
                )
                sinal_atr_rompimento_alta = self.gerar_sinal(
                    [candle], "atr", "rompimento_alta", symbol, timeframe, self.config
                )
                sinal_atr_rompimento_baixa = self.gerar_sinal(
                    [candle], "atr", "rompimento_baixa", symbol, timeframe, self.config
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

            self.banco_dados.conn.commit()
            logger.debug(
                f"Indicadores de volatilidade calculados e sinais gerados para {symbol} - {timeframe}."
            )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular indicadores de volatilidade: {error}")
            dados["volatilidade"] = {
                "bandas_bollinger": None,
                "atr": None,
                "sinais": {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                },
            }
            return True

        return True
