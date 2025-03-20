# outros_indicadores.py
# Plugin para calcular outros indicadores como indicadores Ichimoku Cloud, Fibonacci Retracement e Pivot Points e etc.

import psycopg2
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class OutrosIndicadores(Plugin):
    """
    Plugin para calcular outros indicadores.
    """

    def __init__(self, gerente: GerentePlugin, config=None):
        """
        Inicializa o plugin OutrosIndicadores.

        Args:
            gerente: Instância do gerenciador de plugins
            config: Configurações do sistema
        """
        super().__init__()
        self.nome = "Outros Indicadores"
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

    def calcular_fibonacci_retracement(self, dados):
        """
        Calcula os níveis de Fibonacci Retracement para os dados fornecidos.

        Args:
            dados (list): Lista de candles.

        Returns:
            dict: Um dicionário com os níveis de Fibonacci Retracement.
        """
        try:
            # Coleta valores numéricos válidos
            highs = []
            lows = []

            for candle in dados:
                if len(candle) < 4:
                    continue

                high_val = self._validar_e_converter_valor(candle[2])
                low_val = self._validar_e_converter_valor(candle[3])

                if high_val is not None:
                    highs.append(high_val)
                if low_val is not None:
                    lows.append(low_val)

            if not highs or not lows:
                logger.warning("Dados insuficientes para calcular níveis de Fibonacci")
                return {
                    "0%": 0,
                    "23.6%": 0,
                    "38.2%": 0,
                    "50%": 0,
                    "61.8%": 0,
                    "100%": 0,
                }

            # Obtém o máximo e o mínimo válidos
            maximo = max(highs)
            minimo = min(lows)

            # Calcula a diferença entre o máximo e o mínimo
            diferenca = maximo - minimo

            # Calcula os níveis de Fibonacci Retracement
            niveis = {
                "0%": minimo,
                "23.6%": maximo - diferenca * 0.236,
                "38.2%": maximo - diferenca * 0.382,
                "50%": maximo - diferenca * 0.5,
                "61.8%": maximo - diferenca * 0.618,
                "100%": maximo,
            }

            return niveis

        except Exception as e:
            logger.error(f"Erro ao calcular níveis de Fibonacci: {e}")
            return {"0%": 0, "23.6%": 0, "38.2%": 0, "50%": 0, "61.8%": 0, "100%": 0}

    def calcular_ichimoku(self, dados):
        """
        Calcula o Ichimoku Cloud manualmente.

        Args:
            dados (list): Lista de candles.

        Returns:
            dict: Um dicionário com as listas de valores para cada linha do Ichimoku.
        """
        try:
            # Validar e extrair apenas valores numéricos válidos
            high = []
            low = []
            close = []

            for candle in dados:
                if len(candle) < 5:
                    continue

                h_val = self._validar_e_converter_valor(candle[2])
                l_val = self._validar_e_converter_valor(candle[3])
                c_val = self._validar_e_converter_valor(candle[4])

                if h_val is not None and l_val is not None and c_val is not None:
                    high.append(h_val)
                    low.append(l_val)
                    close.append(c_val)

            # Se não tivermos dados válidos suficientes, retornar arrays vazios
            if len(high) < 3 or len(low) < 3 or len(close) < 3:
                logger.warning("Dados insuficientes para calcular Ichimoku")
                return {
                    "tenkan_sen": np.array([0]),
                    "kijun_sen": np.array([0]),
                    "senkou_span_a": np.array([0]),
                    "senkou_span_b": np.array([0]),
                    "chikou_span": np.array([0]),
                }

            # Converte listas para arrays numpy
            high = np.array(high, dtype=np.float64)
            low = np.array(low, dtype=np.float64)
            close = np.array(close, dtype=np.float64)

            # Parâmetros
            tenkan_sen_period = 9
            kijun_sen_period = 26
            senkou_span_b_period = 52

            # Calcula Tenkan-sen (Linha de Conversão)
            tenkan_sen = np.zeros(len(close))
            for i in range(tenkan_sen_period - 1, len(close)):
                tenkan_sen[i] = (
                    np.max(high[i - tenkan_sen_period + 1 : i + 1])
                    + np.min(low[i - tenkan_sen_period + 1 : i + 1])
                ) / 2

            # Calcula Kijun-sen (Linha Base)
            kijun_sen = np.zeros(len(close))
            for i in range(kijun_sen_period - 1, len(close)):
                kijun_sen[i] = (
                    np.max(high[i - kijun_sen_period + 1 : i + 1])
                    + np.min(low[i - kijun_sen_period + 1 : i + 1])
                ) / 2

            # Calcula Senkou Span A (Primeira Linha Líder)
            senkou_span_a = np.zeros(len(close))
            for i in range(kijun_sen_period - 1, len(close)):
                senkou_span_a[i] = (tenkan_sen[i] + kijun_sen[i]) / 2

            # Calcula Senkou Span B (Segunda Linha Líder)
            senkou_span_b = np.zeros(len(close))
            for i in range(senkou_span_b_period - 1, len(close)):
                senkou_span_b[i] = (
                    np.max(high[i - senkou_span_b_period + 1 : i + 1])
                    + np.min(low[i - senkou_span_b_period + 1 : i + 1])
                ) / 2

            # Calcula Chikou Span (Linha Atrasada)
            chikou_span = np.zeros(len(close))
            chikou_span[:-26] = close[
                26:
            ]  # Desloca o preço de fechamento 26 períodos para trás

            return {
                "tenkan_sen": tenkan_sen,
                "kijun_sen": kijun_sen,
                "senkou_span_a": senkou_span_a,
                "senkou_span_b": senkou_span_b,
                "chikou_span": chikou_span,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Ichimoku Cloud: {e}")
            # Retorna arrays vazios em caso de erro
            return {
                "tenkan_sen": np.array([]),
                "kijun_sen": np.array([]),
                "senkou_span_a": np.array([]),
                "senkou_span_b": np.array([]),
                "chikou_span": np.array([]),
            }

    def calcular_pivot_points(self, dados):
        """
        Calcula os Pivot Points para os dados fornecidos.

        Args:
            dados (list): Lista de candles.

        Returns:
            dict: Um dicionário com os Pivot Points (PP, R1, S1, R2, S2, R3, S3).
        """
        try:
            if not dados or len(dados) == 0:
                logger.warning("Sem dados para calcular Pivot Points")
                return {"PP": 0, "R1": 0, "S1": 0, "R2": 0, "S2": 0, "R3": 0, "S3": 0}

            # Obtém o último candle
            ultimo_candle = dados[-1]
            if len(ultimo_candle) < 5:
                logger.warning(
                    "Estrutura de candle inválida para calcular Pivot Points"
                )
                return {"PP": 0, "R1": 0, "S1": 0, "R2": 0, "S2": 0, "R3": 0, "S3": 0}

            # Converte valores para float com validação
            high = self._validar_e_converter_valor(ultimo_candle[2])
            low = self._validar_e_converter_valor(ultimo_candle[3])
            close = self._validar_e_converter_valor(ultimo_candle[4])

            if high is None or low is None or close is None:
                logger.warning("Valores inválidos para calcular Pivot Points")
                return {"PP": 0, "R1": 0, "S1": 0, "R2": 0, "S2": 0, "R3": 0, "S3": 0}

            # Calcula o Pivot Point (PP)
            pp = (high + low + close) / 3

            # Calcula os níveis de suporte e resistência
            r1 = 2 * pp - low
            s1 = 2 * pp - high
            r2 = pp + (r1 - s1)
            s2 = pp - (r1 - s1)
            r3 = pp + 2 * (r1 - s1)
            s3 = pp - 2 * (r1 - s1)

            return {
                "PP": pp,
                "R1": r1,
                "S1": s1,
                "R2": r2,
                "S2": s2,
                "R3": r3,
                "S3": s3,
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Pivot Points: {e}")
            return {"PP": 0, "R1": 0, "S1": 0, "R2": 0, "S2": 0, "R3": 0, "S3": 0}

    def gerar_sinal(self, dados, indicador, tipo, symbol, timeframe, config):
        """
        Gera um sinal de compra ou venda com base no indicador fornecido,
        seguindo as Regras de Ouro.

        Args:
            dados (list): Lista de candles.
            indicador (str): Nome do indicador ("ichimoku", "fibonacci_retracement" ou "pivot_points").
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

            if indicador == "ichimoku":
                ichimoku = self.calcular_ichimoku(dados)
                if (
                    tipo == "compra"
                    and dados[-1] > ichimoku["senkou_span_a"][-26]
                    and dados[-1] > ichimoku["senkou_span_b"][-26]
                    and ichimoku["tenkan_sen"][-1] > ichimoku["kijun_sen"][-1]
                ):
                    sinal = "compra"
                    stop_loss = min(
                        ichimoku["senkou_span_a"][-26], ichimoku["senkou_span_b"][-26]
                    ) - (dados[-1] - dados[-1]) * (0.1 / alavancagem)
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        2 / alavancagem
                    )
                elif (
                    tipo == "venda"
                    and dados[-1] < ichimoku["senkou_span_a"][-26]
                    and dados[-1] < ichimoku["senkou_span_b"][-26]
                    and ichimoku["tenkan_sen"][-1] < ichimoku["kijun_sen"][-1]
                ):
                    sinal = "venda"
                    stop_loss = max(
                        ichimoku["senkou_span_a"][-26], ichimoku["senkou_span_b"][-26]
                    ) + (dados[-1] - dados[-1]) * (0.1 / alavancagem)
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        2 / alavancagem
                    )

            elif indicador == "fibonacci_retracement":
                niveis = self.calcular_fibonacci_retracement(dados)
                # Lógica para gerar sinais com base nos níveis de Fibonacci Retracement
                if tipo == "suporte":
                    for nivel in ["23.6%", "38.2%", "50%", "61.8%"]:
                        if (
                            dados[-1] <= niveis[nivel] and dados[-2] > niveis[nivel]
                        ):  # Verifica se o candle atual rompeu o nível de suporte
                            sinal = "compra"
                            stop_loss = niveis[nivel] - (dados[-1] - dados[-1]) * (
                                0.1 / alavancagem
                            )  # Stop loss 10% abaixo do nível de suporte
                            take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                                2 / alavancagem
                            )  # Take profit 2 vezes o tamanho do corpo acima do máximo
                            break  # Sai do loop se encontrar um sinal
                elif tipo == "resistencia":
                    for nivel in ["23.6%", "38.2%", "50%", "61.8%"]:
                        if (
                            dados[-1] >= niveis[nivel] and dados[-2] < niveis[nivel]
                        ):  # Verifica se o candle atual rompeu o nível de resistência
                            sinal = "venda"
                            stop_loss = niveis[nivel] + (dados[-1] - dados[-1]) * (
                                0.1 / alavancagem
                            )  # Stop loss 10% acima do nível de resistência
                            take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                                2 / alavancagem
                            )  # Take profit 2 vezes o tamanho do corpo abaixo do mínimo
                            break  # Sai do loop se encontrar um sinal

            elif indicador == "pivot_points":
                pivot_points = self.calcular_pivot_points(dados)
                # Lógica para gerar sinais com base nos Pivot Points
                if tipo == "suporte":
                    for nivel in ["S1", "S2", "S3"]:
                        if (
                            dados[-1] <= pivot_points[nivel]
                            and dados[-2] > pivot_points[nivel]
                        ):  # Verifica se o candle atual rompeu o nível de suporte
                            sinal = "compra"
                            stop_loss = pivot_points[nivel] - (
                                dados[-1] - dados[-1]
                            ) * (
                                0.1 / alavancagem
                            )  # Stop loss 10% abaixo do nível de suporte
                            take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                                2 / alavancagem
                            )  # Take profit 2 vezes o tamanho do corpo acima do máximo
                            break  # Sai do loop se encontrar um sinal
                elif tipo == "resistencia":
                    for nivel in ["R1", "R2", "R3"]:
                        if (
                            dados[-1] >= pivot_points[nivel]
                            and dados[-2] < pivot_points[nivel]
                        ):  # Verifica se o candle atual rompeu o nível de resistência
                            sinal = "venda"
                            stop_loss = pivot_points[nivel] + (
                                dados[-1] - dados[-1]
                            ) * (
                                0.1 / alavancagem
                            )  # Stop loss 10% acima do nível de resistência
                            take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                                2 / alavancagem
                            )  # Take profit 2 vezes o tamanho do corpo abaixo do mínimo
                            break  # Sai do loop se encontrar um sinal

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
        Executa o cálculo dos indicadores, gera sinais de trading e salva os resultados no banco de dados.

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
                dados["outros_indicadores"] = {
                    "ichimoku": None,
                    "fibonacci": None,
                    "pivot_points": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            # Verifica se o banco de dados está disponível e inicializado
            if not self.banco_dados:
                logger.error("Banco de dados não disponível")
                dados["outros_indicadores"] = {
                    "ichimoku": None,
                    "fibonacci": None,
                    "pivot_points": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            # Verificar se a conexão existe no banco de dados
            if not hasattr(self.banco_dados, "conn") or not self.banco_dados.conn:
                logger.error("Conexão com banco de dados não disponível")
                dados["outros_indicadores"] = {
                    "ichimoku": None,
                    "fibonacci": None,
                    "pivot_points": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            cursor = self.banco_dados.conn.cursor()

            for candle in dados:
                # Calcula os indicadores para o candle atual
                ichimoku = self.calcular_ichimoku([candle])
                fibonacci = self.calcular_fibonacci_retracement([candle])
                pivot_points = self.calcular_pivot_points([candle])

                # Gera os sinais de compra e venda para o candle atual
                sinal_ichimoku_compra = self.gerar_sinal(
                    [candle], "ichimoku", "compra", symbol, timeframe, self.config
                )
                sinal_ichimoku_venda = self.gerar_sinal(
                    [candle], "ichimoku", "venda", symbol, timeframe, self.config
                )
                sinal_fibonacci_suporte = self.gerar_sinal(
                    [candle],
                    "fibonacci_retracement",
                    "suporte",
                    symbol,
                    timeframe,
                    self.config,
                )
                sinal_fibonacci_resistencia = self.gerar_sinal(
                    [candle],
                    "fibonacci_retracement",
                    "resistencia",
                    symbol,
                    timeframe,
                    self.config,
                )
                sinal_pivot_points_suporte = self.gerar_sinal(
                    [candle], "pivot_points", "suporte", symbol, timeframe, self.config
                )
                sinal_pivot_points_resistencia = self.gerar_sinal(
                    [candle],
                    "pivot_points",
                    "resistencia",
                    symbol,
                    timeframe,
                    self.config,
                )

                # Salva os resultados no banco de dados para o candle atual
                timestamp = int(candle / 1000)  # Converte o timestamp para segundos
                cursor.execute(
                    """
                    INSERT INTO outros_indicadores (
                        symbol, timeframe, timestamp,
                        tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span,
                        fibonacci_23_6, fibonacci_38_2, fibonacci_50, fibonacci_61_8,
                        pivot_point, r1, s1, r2, s2, r3, s3,
                        sinal_ichimoku_compra, stop_loss_ichimoku_compra, take_profit_ichimoku_compra,
                        sinal_ichimoku_venda, stop_loss_ichimoku_venda, take_profit_ichimoku_venda,
                        sinal_fibonacci_suporte, stop_loss_fibonacci_suporte, take_profit_fibonacci_suporte,
                        sinal_fibonacci_resistencia, stop_loss_fibonacci_resistencia, take_profit_fibonacci_resistencia,
                        sinal_pivot_points_suporte, stop_loss_pivot_points_suporte, take_profit_pivot_points_suporte,
                        sinal_pivot_points_resistencia, stop_loss_pivot_points_resistencia, take_profit_pivot_points_resistencia
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
                    SET tenkan_sen = EXCLUDED.tenkan_sen, kijun_sen = EXCLUDED.kijun_sen, senkou_span_a = EXCLUDED.senkou_span_a,
                        senkou_span_b = EXCLUDED.senkou_span_b, chikou_span = EXCLUDED.chikou_span,
                        fibonacci_23_6 = EXCLUDED.fibonacci_23_6, fibonacci_38_2 = EXCLUDED.fibonacci_38_2,
                        fibonacci_50 = EXCLUDED.fibonacci_50, fibonacci_61_8 = EXCLUDED.fibonacci_61_8,
                        pivot_point = EXCLUDED.pivot_point, r1 = EXCLUDED.r1, s1 = EXCLUDED.s1, r2 = EXCLUDED.r2, s2 = EXCLUDED.s2, r3 = EXCLUDED.r3, s3 = EXCLUDED.s3,
                        sinal_ichimoku_compra = EXCLUDED.sinal_ichimoku_compra, stop_loss_ichimoku_compra = EXCLUDED.stop_loss_ichimoku_compra, take_profit_ichimoku_compra = EXCLUDED.take_profit_ichimoku_compra,
                        sinal_ichimoku_venda = EXCLUDED.sinal_ichimoku_venda, stop_loss_ichimoku_venda = EXCLUDED.stop_loss_ichimoku_venda, take_profit_ichimoku_venda = EXCLUDED.take_profit_ichimoku_venda,
                        sinal_fibonacci_suporte = EXCLUDED.sinal_fibonacci_suporte, stop_loss_fibonacci_suporte = EXCLUDED.stop_loss_fibonacci_suporte, take_profit_fibonacci_suporte = EXCLUDED.take_profit_fibonacci_suporte,
                        sinal_fibonacci_resistencia = EXCLUDED.sinal_fibonacci_resistencia, stop_loss_fibonacci_resistencia = EXCLUDED.stop_loss_fibonacci_resistencia, take_profit_fibonacci_resistencia = EXCLUDED.take_profit_fibonacci_resistencia,
                        sinal_pivot_points_suporte = EXCLUDED.sinal_pivot_points_suporte, stop_loss_pivot_points_suporte = EXCLUDED.stop_loss_pivot_points_suporte, take_profit_pivot_points_suporte = EXCLUDED.take_profit_pivot_points_suporte,
                        sinal_pivot_points_resistencia = EXCLUDED.sinal_pivot_points_resistencia, stop_loss_pivot_points_resistencia = EXCLUDED.stop_loss_pivot_points_resistencia, take_profit_pivot_points_resistencia = EXCLUDED.take_profit_pivot_points_resistencia;
                    """,
                    (
                        symbol,
                        timeframe,
                        timestamp,
                        ichimoku["tenkan_sen"][-1],
                        ichimoku["kijun_sen"][-1],
                        ichimoku["senkou_span_a"][-1],
                        ichimoku["senkou_span_b"][-1],
                        ichimoku["chikou_span"][-1],
                        fibonacci["23.6%"],
                        fibonacci["38.2%"],
                        fibonacci["50%"],
                        fibonacci["61.8%"],
                        pivot_points["PP"],
                        pivot_points["R1"],
                        pivot_points["S1"],
                        pivot_points["R2"],
                        pivot_points["S2"],
                        pivot_points["R3"],
                        pivot_points["S3"],
                        sinal_ichimoku_compra["sinal"],
                        sinal_ichimoku_compra["stop_loss"],
                        sinal_ichimoku_compra["take_profit"],
                        sinal_ichimoku_venda["sinal"],
                        sinal_ichimoku_venda["stop_loss"],
                        sinal_ichimoku_venda["take_profit"],
                        sinal_fibonacci_suporte["sinal"],
                        sinal_fibonacci_suporte["stop_loss"],
                        sinal_fibonacci_suporte["take_profit"],
                        sinal_fibonacci_resistencia["sinal"],
                        sinal_fibonacci_resistencia["stop_loss"],
                        sinal_fibonacci_resistencia["take_profit"],
                        sinal_pivot_points_suporte["sinal"],
                        sinal_pivot_points_suporte["stop_loss"],
                        sinal_pivot_points_suporte["take_profit"],
                        sinal_pivot_points_resistencia["sinal"],
                        sinal_pivot_points_resistencia["stop_loss"],
                        sinal_pivot_points_resistencia["take_profit"],
                    ),
                )

            self.banco_dados.conn.commit()
            logger.debug(
                f"Outros indicadores calculados e sinais gerados para {symbol} - {timeframe}."
            )
            return True

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular outros indicadores: {error}")
            dados["outros_indicadores"] = {
                "ichimoku": None,
                "fibonacci": None,
                "pivot_points": None,
                "sinais": {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                },
            }
            return True
