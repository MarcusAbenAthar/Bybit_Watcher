from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import psycopg2
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresOsciladores(Plugin):
    def __init__(self, gerente: GerentePlugin, config=None):
        """
        Inicializa o plugin IndicadoresOsciladores.

        Args:
            gerente: Instância do gerenciador de plugins
            config: Configurações do sistema
        """
        super().__init__()
        self.nome = "Indicadores Osciladores"
        self.config = config
        self.gerente = gerente
        # Acessa o plugin de cálculo de alavancagem através do gerente
        self.calculo_alavancagem = self.gerente.obter_calculo_alavancagem()
        # Acesso ao banco de dados através do gerente
        self.banco_dados = self.gerente.obter_banco_dados()

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

        # Extrai os valores de fechamento dos candles e converte para numpy array
        try:
            fechamentos = []
            for candle in dados:
                if candle[4] is None or str(candle[4]).strip() == "":
                    continue
                try:
                    valor = float(str(candle[4]).replace("e", "").replace("E", ""))
                    fechamentos.append(valor)
                except (ValueError, TypeError):
                    continue

            if not fechamentos:
                logger.warning("Nenhum dado válido para calcular RSI")
                return np.array([])

            fechamentos = np.array(fechamentos, dtype=np.float64)
        except Exception as e:
            logger.error(f"Erro ao converter dados para float: {e}")
            return np.array([])

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

        # Extrai e valida os valores
        try:
            high = []
            low = []
            close = []

            for candle in dados:
                if any(str(val).strip() == "" or val is None for val in candle[2:5]):
                    continue
                try:
                    h = float(str(candle[2]).replace("e", "").replace("E", ""))
                    l = float(str(candle[3]).replace("e", "").replace("E", ""))
                    c = float(str(candle[4]).replace("e", "").replace("E", ""))
                    high.append(h)
                    low.append(l)
                    close.append(c)
                except (ValueError, TypeError):
                    continue

            if not high or not low or not close:
                logger.warning("Dados insuficientes para calcular indicadores")
                return np.array([]), np.array([])

            # Converte para numpy arrays
            high = np.array(high, dtype=np.float64)
            low = np.array(low, dtype=np.float64)
            close = np.array(close, dtype=np.float64)

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
        except Exception as e:
            logger.error(f"Erro ao calcular estocástico: {e}")
            return np.array([]), np.array([])

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

    def calcular_volatilidade(self, dados, periodo=14):
        """
        Calcula a volatilidade dos preços usando desvio padrão.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período para cálculo da volatilidade.

        Returns:
            float: Valor da volatilidade normalizado entre 0 e 1.
        """
        try:
            # Verifica se há dados suficientes
            if len(dados) < periodo:
                return 0.0

            # Extrai os preços de fechamento e converte para numpy array
            fechamentos = np.array(
                [float(candle[4]) for candle in dados], dtype=np.float64
            )

            # Calcula o desvio padrão
            std = talib.STDDEV(fechamentos, timeperiod=periodo)

            # Normaliza o resultado (último valor do desvio padrão)
            if std is not None and len(std) > 0:
                volatilidade = float(std[-1]) / float(fechamentos[-1])
                return min(max(volatilidade, 0.0), 1.0)  # Limita entre 0 e 1

            return 0.0

        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {e}")
            return 0.0

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

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo dos indicadores osciladores.

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

            # Validação do tipo do parâmetro 'dados'
            if not isinstance(dados, dict):
                logger.error("Parâmetro 'dados' está ausente ou inválido")
                return False
            # Validação dos parâmetros
            if not all([dados, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                dados["osciladores"] = {
                    "rsi": None,
                    "estocastico": None,
                    "mfi": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            # Calcula os indicadores
            try:
                rsi = self.calcular_rsi(dados, symbol, timeframe)
                estocastico_lento, estocastico_rapido = self.calcular_estocastico(
                    dados, timeframe
                )
                mfi = self.calcular_mfi(dados)

                # Atualiza o dicionário de dados
                dados["osciladores"] = {
                    "rsi": rsi[-1] if rsi is not None else None,
                    "estocastico": {
                        "lento": (
                            estocastico_lento[-1]
                            if estocastico_lento is not None
                            else None
                        ),
                        "rapido": (
                            estocastico_rapido[-1]
                            if estocastico_rapido is not None
                            else None
                        ),
                    },
                    "mfi": mfi[-1] if mfi is not None else None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }

                # Tenta salvar no banco se disponível
                if self.banco_dados and self.banco_dados.conn:
                    try:
                        cursor = self.banco_dados.conn.cursor()
                        timestamp = int(dados[-1][0] / 1000)
                        cursor.execute(
                            """
                            INSERT INTO indicadores_osciladores (
                                symbol, timeframe, timestamp, rsi, estocastico_lento, 
                                estocastico_rapido, mfi
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, timeframe, timestamp) 
                            DO UPDATE SET 
                                rsi = EXCLUDED.rsi,
                                estocastico_lento = EXCLUDED.estocastico_lento,
                                estocastico_rapido = EXCLUDED.estocastico_rapido,
                                mfi = EXCLUDED.mfi
                            """,
                            (
                                symbol,
                                timeframe,
                                timestamp,
                                dados["osciladores"]["rsi"],
                                dados["osciladores"]["estocastico"]["lento"],
                                dados["osciladores"]["estocastico"]["rapido"],
                                dados["osciladores"]["mfi"],
                            ),
                        )
                        self.banco_dados.conn.commit()
                    except Exception as e:
                        logger.error(f"Erro ao salvar no banco: {e}")

            except Exception as e:
                logger.error(f"Erro ao calcular indicadores: {e}")
                dados["osciladores"] = {
                    "rsi": None,
                    "estocastico": None,
                    "mfi": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }

            return True

        except Exception as e:
            logger.error(f"Erro ao executar indicadores osciladores: {e}")
            dados["osciladores"] = {
                "rsi": None,
                "estocastico": None,
                "mfi": None,
                "sinais": {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                },
            }
            return True
