from plugins.gerenciadores import gerenciador_banco
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import pandas as pd
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
        self.gerenciador_banco = gerenciador_banco

    def calcular_fibonacci_retracement(self, dados):
        """
        Calcula os níveis de Fibonacci Retracement para os dados fornecidos.

        Args:
            dados (list): Lista de candles.

        Returns:
            dict: Um dicionário com os níveis de Fibonacci Retracement.
        """
        # Obtém o máximo e o mínimo do período
        maximo = max([candle[2] for candle in dados])
        minimo = min([candle[3] for candle in dados])

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

    def calcular_ichimoku(self, dados):
        """
        Calcula o Ichimoku Cloud para os dados fornecidos, usando a biblioteca pandas-ta.

        Args:
            dados (list): Lista de candles.

        Returns:
            dict: Um dicionário com as listas de valores para cada linha do Ichimoku.
        """
        # Converter dados para DataFrame do pandas
        df = pd.DataFrame(
            dados, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Calcular o Ichimoku Cloud
        ichimoku = df.ta.ichimoku()

        return {
            "tenkan_sen": ichimoku["TENKAN"].values.tolist(),
            "kijun_sen": ichimoku["KIJUN"].values.tolist(),
            "senkou_span_a": ichimoku["SPAN_A"].values.tolist(),
            "senkou_span_b": ichimoku["SPAN_B"].values.tolist(),
            "chikou_span": ichimoku["CHIKOU"].values.tolist(),
        }

    def calcular_pivot_points(self, dados):
        """
        Calcula os Pivot Points para os dados fornecidos.

        Args:
            dados (list): Lista de candles.

        Returns:
            dict: Um dicionário com os Pivot Points (PP, R1, S1, R2, S2, R3, S3).
        """
        # Obtém o último candle
        ultimo_candle = dados[-1]
        high = ultimo_candle[2]
        low = ultimo_candle[3]
        close = ultimo_candle[4]

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

            # Verifica se o gerenciador_banco está disponível
            if not self.gerenciador_banco:
                logger.error("Gerenciador de banco não disponível")
                return False

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

                # Salva os resultados chamando o método no gerenciador_banco
                self.gerenciador_banco.salvar_dados_outros_indicadores(
                    [
                        {
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "timestamp": timestamp,
                            "tenkan_sen": ichimoku["tenkan_sen"][-1],
                            "kijun_sen": ichimoku["kijun_sen"][-1],
                            "senkou_span_a": ichimoku["senkou_span_a"][-1],
                            "senkou_span_b": ichimoku["senkou_span_b"][-1],
                            "chikou_span": ichimoku["chikou_span"][-1],
                            "fibonacci_23_6": fibonacci["23.6%"],
                            "fibonacci_38_2": fibonacci["38.2%"],
                            "fibonacci_50": fibonacci["50%"],
                            "fibonacci_61_8": fibonacci["61.8%"],
                            "pivot_point": pivot_points["PP"],
                            "r1": pivot_points["R1"],
                            "s1": pivot_points["S1"],
                            "r2": pivot_points["R2"],
                            "s2": pivot_points["S2"],
                            "r3": pivot_points["R3"],
                            "s3": pivot_points["S3"],
                            "sinal_ichimoku_compra": sinal_ichimoku_compra["sinal"],
                            "stop_loss_ichimoku_compra": sinal_ichimoku_compra[
                                "stop_loss"
                            ],
                            "take_profit_ichimoku_compra": sinal_ichimoku_compra[
                                "take_profit"
                            ],
                            "sinal_ichimoku_venda": sinal_ichimoku_venda["sinal"],
                            "stop_loss_ichimoku_venda": sinal_ichimoku_venda[
                                "stop_loss"
                            ],
                            "take_profit_ichimoku_venda": sinal_ichimoku_venda[
                                "take_profit"
                            ],
                            "sinal_fibonacci_suporte": sinal_fibonacci_suporte["sinal"],
                            "stop_loss_fibonacci_suporte": sinal_fibonacci_suporte[
                                "stop_loss"
                            ],
                            "take_profit_fibonacci_suporte": sinal_fibonacci_suporte[
                                "take_profit"
                            ],
                            "sinal_fibonacci_resistencia": sinal_fibonacci_resistencia[
                                "sinal"
                            ],
                            "stop_loss_fibonacci_resistencia": sinal_fibonacci_resistencia[
                                "stop_loss"
                            ],
                            "take_profit_fibonacci_resistencia": sinal_fibonacci_resistencia[
                                "take_profit"
                            ],
                            "sinal_pivot_points_suporte": sinal_pivot_points_suporte[
                                "sinal"
                            ],
                            "stop_loss_pivot_points_suporte": sinal_pivot_points_suporte[
                                "stop_loss"
                            ],
                            "take_profit_pivot_points_suporte": sinal_pivot_points_suporte[
                                "take_profit"
                            ],
                            "sinal_pivot_points_resistencia": sinal_pivot_points_resistencia[
                                "sinal"
                            ],
                            "stop_loss_pivot_points_resistencia": sinal_pivot_points_resistencia[
                                "stop_loss"
                            ],
                            "take_profit_pivot_points_resistencia": sinal_pivot_points_resistencia[
                                "take_profit"
                            ],
                        }
                    ]
                )
            return True

        except Exception as e:
            logger.error(f"Erro ao executar outros indicadores: {e}")
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

    # def executar(self, *args, **kwargs) -> bool:
    #     """
    #     Executa o cálculo dos indicadores, gera sinais de trading e salva os resultados no banco de dados.

    #     Args:
    #         *args: Argumentos posicionais ignorados
    #         **kwargs: Argumentos nomeados contendo:
    #             dados (list): Lista de candles
    #             symbol (str): Símbolo do par
    #             timeframe (str): Timeframe da análise
    #             config (dict): Configurações do bot

    #     Returns:
    #         bool: True se executado com sucesso
    #     """
    #     try:
    #         # Extrai os parâmetros necessários
    #         dados = kwargs.get("dados")
    #         symbol = kwargs.get("symbol")
    #         timeframe = kwargs.get("timeframe")

    #         # Validação dos parâmetros
    #         if not all([dados, symbol, timeframe]):
    #             logger.error("Parâmetros necessários não fornecidos")
    #             dados["outros_indicadores"] = {
    #                 "ichimoku": None,
    #                 "fibonacci": None,
    #                 "pivot_points": None,
    #                 "sinais": {
    #                     "direcao": "NEUTRO",
    #                     "forca": "FRACA",
    #                     "confianca": 0,
    #                 },
    #             }
    #             return True

    #         # Verifica se o banco de dados está disponível e obtém a instância do BancoDados
    #         logger.error(f"Tipo de banco_dados: {type(self.banco_dados)}")
    #         logger.error(dir(self.gerente))  # Mostra os métodos disponíveis

    #         banco_dados = self.gerente.obter_banco_dados()
    #         if not banco_dados or not banco_dados.obter_conexao():
    #             logger.error("Banco de dados não disponível")
    #             dados["outros_indicadores"] = {
    #                 "ichimoku": None,
    #                 "fibonacci": None,
    #                 "pivot_points": None,
    #                 "sinais": {
    #                     "direcao": "NEUTRO",
    #                     "forca": "FRACA",
    #                     "confianca": 0,
    #                 },
    #             }
    #             return True

    #         cursor = self.banco_dados.conn.cursor()

    #         for candle in dados:
    #             # Calcula os indicadores para o candle atual
    #             ichimoku = self.calcular_ichimoku([candle])
    #             fibonacci = self.calcular_fibonacci_retracement([candle])
    #             pivot_points = self.calcular_pivot_points([candle])

    #             # Gera os sinais de compra e venda para o candle atual
    #             sinal_ichimoku_compra = self.gerar_sinal(
    #                 [candle], "ichimoku", "compra", symbol, timeframe, self.config
    #             )
    #             sinal_ichimoku_venda = self.gerar_sinal(
    #                 [candle], "ichimoku", "venda", symbol, timeframe, self.config
    #             )
    #             sinal_fibonacci_suporte = self.gerar_sinal(
    #                 [candle],
    #                 "fibonacci_retracement",
    #                 "suporte",
    #                 symbol,
    #                 timeframe,
    #                 self.config,
    #             )
    #             sinal_fibonacci_resistencia = self.gerar_sinal(
    #                 [candle],
    #                 "fibonacci_retracement",
    #                 "resistencia",
    #                 symbol,
    #                 timeframe,
    #                 self.config,
    #             )
    #             sinal_pivot_points_suporte = self.gerar_sinal(
    #                 [candle], "pivot_points", "suporte", symbol, timeframe, self.config
    #             )
    #             sinal_pivot_points_resistencia = self.gerar_sinal(
    #                 [candle],
    #                 "pivot_points",
    #                 "resistencia",
    #                 symbol,
    #                 timeframe,
    #                 self.config,
    #             )

    #             # Salva os resultados no banco de dados para o candle atual
    #             timestamp = int(candle / 1000)  # Converte o timestamp para segundos
    #             cursor.execute(
    #                 """
    #                 INSERT INTO outros_indicadores (
    #                     symbol, timeframe, timestamp,
    #                     tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span,
    #                     fibonacci_23_6, fibonacci_38_2, fibonacci_50, fibonacci_61_8,
    #                     pivot_point, r1, s1, r2, s2, r3, s3,
    #                     sinal_ichimoku_compra, stop_loss_ichimoku_compra, take_profit_ichimoku_compra,
    #                     sinal_ichimoku_venda, stop_loss_ichimoku_venda, take_profit_ichimoku_venda,
    #                     sinal_fibonacci_suporte, stop_loss_fibonacci_suporte, take_profit_fibonacci_suporte,
    #                     sinal_fibonacci_resistencia, stop_loss_fibonacci_resistencia, take_profit_fibonacci_resistencia,
    #                     sinal_pivot_points_suporte, stop_loss_pivot_points_suporte, take_profit_pivot_points_suporte,
    #                     sinal_pivot_points_resistencia, stop_loss_pivot_points_resistencia, take_profit_pivot_points_resistencia
    #                 )
    #                 VALUES (
    #                     %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    #                 )
    #                 ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
    #                 SET tenkan_sen = EXCLUDED.tenkan_sen, kijun_sen = EXCLUDED.kijun_sen, senkou_span_a = EXCLUDED.senkou_span_a,
    #                     senkou_span_b = EXCLUDED.senkou_span_b, chikou_span = EXCLUDED.chikou_span,
    #                     fibonacci_23_6 = EXCLUDED.fibonacci_23_6, fibonacci_38_2 = EXCLUDED.fibonacci_38_2,
    #                     fibonacci_50 = EXCLUDED.fibonacci_50, fibonacci_61_8 = EXCLUDED.fibonacci_61_8,
    #                     pivot_point = EXCLUDED.pivot_point, r1 = EXCLUDED.r1, s1 = EXCLUDED.s1, r2 = EXCLUDED.r2, s2 = EXCLUDED.s2, r3 = EXCLUDED.r3, s3 = EXCLUDED.s3,
    #                     sinal_ichimoku_compra = EXCLUDED.sinal_ichimoku_compra, stop_loss_ichimoku_compra = EXCLUDED.stop_loss_ichimoku_compra, take_profit_ichimoku_compra = EXCLUDED.take_profit_ichimoku_compra,
    #                     sinal_ichimoku_venda = EXCLUDED.sinal_ichimoku_venda, stop_loss_ichimoku_venda = EXCLUDED.stop_loss_ichimoku_venda, take_profit_ichimoku_venda = EXCLUDED.take_profit_ichimoku_venda,
    #                     sinal_fibonacci_suporte = EXCLUDED.sinal_fibonacci_suporte, stop_loss_fibonacci_suporte = EXCLUDED.stop_loss_fibonacci_suporte, take_profit_fibonacci_suporte = EXCLUDED.take_profit_fibonacci_suporte,
    #                     sinal_fibonacci_resistencia = EXCLUDED.sinal_fibonacci_resistencia, stop_loss_fibonacci_resistencia = EXCLUDED.stop_loss_fibonacci_resistencia, take_profit_fibonacci_resistencia = EXCLUDED.take_profit_fibonacci_resistencia,
    #                     sinal_pivot_points_suporte = EXCLUDED.sinal_pivot_points_suporte, stop_loss_pivot_points_suporte = EXCLUDED.stop_loss_pivot_points_suporte, take_profit_pivot_points_suporte = EXCLUDED.take_profit_pivot_points_suporte,
    #                     sinal_pivot_points_resistencia = EXCLUDED.sinal_pivot_points_resistencia, stop_loss_pivot_points_resistencia = EXCLUDED.stop_loss_pivot_points_resistencia, take_profit_pivot_points_resistencia = EXCLUDED.take_profit_pivot_points_resistencia;
    #                 """,
    #                 (
    #                     symbol,
    #                     timeframe,
    #                     timestamp,
    #                     ichimoku["tenkan_sen"][-1],
    #                     ichimoku["kijun_sen"][-1],
    #                     ichimoku["senkou_span_a"][-1],
    #                     ichimoku["senkou_span_b"][-1],
    #                     ichimoku["chikou_span"][-1],
    #                     fibonacci["23.6%"],
    #                     fibonacci["38.2%"],
    #                     fibonacci["50%"],
    #                     fibonacci["61.8%"],
    #                     pivot_points["PP"],
    #                     pivot_points["R1"],
    #                     pivot_points["S1"],
    #                     pivot_points["R2"],
    #                     pivot_points["S2"],
    #                     pivot_points["R3"],
    #                     pivot_points["S3"],
    #                     sinal_ichimoku_compra["sinal"],
    #                     sinal_ichimoku_compra["stop_loss"],
    #                     sinal_ichimoku_compra["take_profit"],
    #                     sinal_ichimoku_venda["sinal"],
    #                     sinal_ichimoku_venda["stop_loss"],
    #                     sinal_ichimoku_venda["take_profit"],
    #                     sinal_fibonacci_suporte["sinal"],
    #                     sinal_fibonacci_suporte["stop_loss"],
    #                     sinal_fibonacci_suporte["take_profit"],
    #                     sinal_fibonacci_resistencia["sinal"],
    #                     sinal_fibonacci_resistencia["stop_loss"],
    #                     sinal_fibonacci_resistencia["take_profit"],
    #                     sinal_pivot_points_suporte["sinal"],
    #                     sinal_pivot_points_suporte["stop_loss"],
    #                     sinal_pivot_points_suporte["take_profit"],
    #                     sinal_pivot_points_resistencia["sinal"],
    #                     sinal_pivot_points_resistencia["stop_loss"],
    #                     sinal_pivot_points_resistencia["take_profit"],
    #                 ),
    #             )

    #         self.banco_dados.conn.commit()
    #         logger.debug(
    #             f"Outros indicadores calculados e sinais gerados para {symbol} - {timeframe}."
    #         )
    #         return True

    #     except (Exception, psycopg2.Error) as error:
    #         logger.error(f"Erro ao calcular outros indicadores: {error}")
    #         dados["outros_indicadores"] = {
    #             "ichimoku": None,
    #             "fibonacci": None,
    #             "pivot_points": None,
    #             "sinais": {
    #                 "direcao": "NEUTRO",
    #                 "forca": "FRACA",
    #                 "confianca": 0,
    #             },
    #         }
    #         return True
