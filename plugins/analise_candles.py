import logging

logger = logging.getLogger(__name__)

import psycopg2
from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_calculo_alavancagem, obter_banco_dados
import talib
from utils.padroes_candles import PADROES_CANDLES
import numpy as np


class AnaliseCandles(Plugin):
    """
    Plugin para analisar os candles e identificar padrões.
    """

    def __init__(self):
        super().__init__()
        self.nome = "Análise de Candles"
        self.descricao = "Plugin para análise de padrões de candles"
        self.calculo_alavancagem = obter_calculo_alavancagem()

    def identificar_padrao(self, candle):
        """
        Identifica o padrão do candle usando TA-Lib.
        """
        if not candle or len(candle) < 4:
            logger.warning("Dados de candle inválidos.")
            return None

        try:
            # Desempacota os valores do candle diretamente
            abertura, fechamento, maximo, minimo = candle

            # Itera pelas funções do grupo "Pattern Recognition" do TA-Lib
            for nome_funcao in talib.get_function_groups()["Pattern Recognition"]:
                # Obtém a função do TA-Lib
                funcao_talib = getattr(talib, nome_funcao)

                # Executa a função com os dados do candle
                resultado_padrao = funcao_talib(abertura, maximo, minimo, fechamento)

                if resultado_padrao != 0:
                    # Verifica se o nome da função começa com 'CDL' antes de remover
                    nome_padrao = (
                        nome_funcao[3:].lower()
                        if nome_funcao.startswith("CDL")
                        else nome_funcao.lower()
                    )
                    return nome_padrao

            return None

        except Exception as e:
            logger.error(f"Erro ao identificar padrão com a função {nome_funcao}: {e}")
            return None

    def classificar_candle(self, candle):
        """
        Classifica o candle como alta, baixa ou indecisão.
        """
        try:
            if not candle or len(candle) < 4:
                return "indecisão"

            abertura, fechamento, maximo, minimo = candle

            # Calcula o tamanho do corpo do candle
            tamanho_corpo = abs(fechamento - abertura)
            limite_corpo_pequeno = 0.1 * (maximo - minimo)

            if tamanho_corpo <= limite_corpo_pequeno:
                return "indecisão"
            elif fechamento > abertura:
                return "alta"
            else:
                return "baixa"

        except Exception as e:
            logger.error(f"Erro ao classificar candle: {e}")
            return "indecisão"

    def gerar_sinal(self, candle, padrao, classificacao, symbol, timeframe, config):
        """
        Gera sinal baseado no padrão e classificação do candle.
        """
        try:
            if not padrao or not classificacao:
                return self._sinal_padrao()

            # Busca o padrão no PADROES_CANDLES
            chave_padrao = f"{padrao}_{classificacao}"
            if chave_padrao not in PADROES_CANDLES:
                return self._sinal_padrao()

            padrao_info = PADROES_CANDLES[chave_padrao]

            # Calcula stop loss e take profit
            try:
                alavancagem = self.calculo_alavancagem.calcular_alavancagem(
                    candle, symbol, timeframe, config
                )
                stop_loss = padrao_info["stop_loss"](candle, alavancagem)
                take_profit = padrao_info["take_profit"](candle, alavancagem)
            except Exception as e:
                logger.error(f"Erro ao calcular níveis: {e}")
                return self._sinal_padrao()

            return {
                "sinal": padrao_info["sinal"],
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "forca": self.calcular_forca_padrao(candle, padrao),
                "confianca": self.calcular_confianca(candle, padrao),
            }

        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return self._sinal_padrao()

    def _sinal_padrao(self):
        """Retorna um sinal padrão vazio."""
        return {
            "sinal": None,
            "stop_loss": None,
            "take_profit": None,
            "forca": 0,
            "confianca": 0,
        }

    def executar(self, dados, symbol, timeframe):
        """
        Executa a análise dos candles.

        Args:
            dados (list): Lista de candles.
            symbol (str): Símbolo do par de moedas.
            timeframe (str): Timeframe da análise.
        """
        logger.debug(f"Iniciando análise de candles para {symbol} - {timeframe}")
        try:
            # Passar symbol e timeframe para analisar_candles
            return self.analisar_candles(dados, symbol, timeframe)
        except Exception as e:
            logger.error(f"Erro ao analisar candles: {e}")
            raise

    def _calcular_tamanho_relativo_e_multiplicador(self, candle, padrao):
        """
        Função auxiliar para calcular o tamanho relativo do candle e o multiplicador.
        """
        if not candle or len(candle) < 4:
            return 0, 1.0

        abertura, fechamento, maximo, minimo = candle
        tamanho_corpo = abs(float(fechamento) - float(abertura))
        tamanho_total = float(maximo) - float(minimo)

        if tamanho_total <= 0:
            return 0, 1.0

        tamanho_relativo = (tamanho_corpo / tamanho_total) * 100

        multiplicador = PADROES_CANDLES.get(f"{padrao}_alta", {}).get("peso", 1.0)
        multiplicador = PADROES_CANDLES.get(f"{padrao}_baixa", {}).get(
            "peso", multiplicador
        )

        return tamanho_relativo, multiplicador

    def calcular_forca_padrao(self, candle, padrao):
        """
        Calcula a força do padrão identificado.
        """
        try:
            tamanho_relativo, multiplicador = (
                self._calcular_tamanho_relativo_e_multiplicador(candle, padrao)
            )
            forca = min(100, tamanho_relativo * multiplicador)
            logger.debug(f"Força do padrão {padrao}: {forca:.2f}")
            return forca

        except Exception as e:
            logger.error(f"Erro ao calcular força do padrão: {e}")
            return 0

    def calcular_confianca(self, candle, padrao):
        """
        Calcula a confiança do padrão identificado.
        """
        try:
            tamanho_relativo, multiplicador = (
                self._calcular_tamanho_relativo_e_multiplicador(candle, padrao)
            )
            confianca = min(100, tamanho_relativo * multiplicador)
            logger.debug(f"Confiança do padrão {padrao}: {confianca:.2f}")
            return confianca

        except Exception as e:
            logger.error(f"Erro ao calcular confiança do padrão: {e}")
            return 0

    def analisar_candles(self, dados, symbol, timeframe):
        """
        Analisa os padrões nos candles, classifica os candles e gera sinais.

        Args:
            dados (list): Lista de candles para análise.
            symbol (str): Símbolo do par de moedas.
            timeframe (str): Timeframe da análise.
        """
        try:
            # Verificar se dados é válido
            if not dados or not isinstance(dados, (list, tuple)):
                logger.warning("Dados inválidos para análise de candles")
                return {}

            # Converter apenas os dados numéricos para numpy array
            dados_np = []
            for candle in dados:
                # Pegar apenas os valores OHLCV, ignorando symbol e timeframe
                valores = [
                    float(v) for v in candle[2:]
                ]  # Começar do índice 2 (timestamp)
                dados_np.append(valores)

            dados_np = np.array(dados_np, dtype=np.float64)

            # Extrair OHLC (ajustando índices após remover symbol/timeframe)
            opens = dados_np[:, 1]
            highs = dados_np[:, 2]
            lows = dados_np[:, 3]
            closes = dados_np[:, 4]

            # Analisar padrões usando TALib
            resultados = {}

            # Movendo a declaração da variável nome_funcao para fora do try
            for nome_funcao in talib.get_function_groups()["Pattern Recognition"]:
                try:
                    # Obter a função do talib
                    funcao_talib = getattr(talib, nome_funcao)

                    # Executar a função com os dados OHLC
                    resultado_padrao = funcao_talib(opens, highs, lows, closes)

                    # Converter o nome da função para o formato do padroes_candles.py
                    nome_padrao = nome_funcao.lower().replace("cdl", "")

                    # Adicionar o resultado ao dicionário
                    resultados[nome_padrao] = resultado_padrao
                except Exception as e:
                    logger.error(f"Erro ao analisar padrão {nome_funcao}: {e}")

            # 2. Iterar pelos candles e gerar sinais
            for candle in dados:
                padrao_candle = self.identificar_padrao(candle)
                classificacao_candle = self.classificar_candle(candle)

                if padrao_candle:
                    # 3. Gerar sinal
                    sinal = self.gerar_sinal(
                        candle,
                        padrao_candle,
                        classificacao_candle,
                        symbol,
                        timeframe,
                        self.config,
                    )

                    if sinal:
                        # 4. Salvar sinal no banco de dados
                        self.banco_dados.inserir_dados(
                            "analise_candles",
                            {
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "timestamp": candle,  # Timestamp do candle
                                "padrao": padrao_candle,
                                "classificacao": classificacao_candle,
                                "sinal": sinal["sinal"],
                                "stop_loss": sinal["stop_loss"],
                                "take_profit": sinal["take_profit"],
                            },
                        )

            return resultados

        except Exception as e:
            # Capturar a exceção e logar o erro
            logger.error(f"Erro na análise de candles: {e}")
            raise
