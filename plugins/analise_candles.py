import logging

logger = logging.getLogger(__name__)

from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_calculo_alavancagem
import talib
from utils.padroes_candles import PADROES_CANDLES
import numpy as np
from plugins.gerenciador_banco import gerenciador_banco
from plugins.validador_dados import ValidadorDados


class AnaliseCandles(Plugin):
    """
    Plugin para analisar os candles e identificar padrões.
    """

    def __init__(self):
        super().__init__()
        self.nome = "Análise de Candles"
        self.descricao = "Plugin para análise de padrões de candles"
        self.calculo_alavancagem = obter_calculo_alavancagem()
        self.validador = ValidadorDados()

    def identificar_padrao(self, candle):
        """
        Identifica o padrão do candle usando TA-Lib.

        Args:
            candle (list): Lista com dados OHLC do candle
                [timestamp, open, high, low, close, volume]

        Returns:
            str: Nome do padrão identificado ou None
        """
        if not isinstance(candle, (list, tuple)) or len(candle) < 6:
            logger.warning(f"Dados de candle inválidos: {candle}")
            return None

        try:
            # Debug log para verificar a estrutura dos dados
            logger.debug(f"Dados do candle recebidos: {candle}")

            # Extrair valores OHLC do candle, garantindo que são números
            try:
                # Assegurar que estamos pegando os índices corretos
                open_price = float(candle[2])  # Ajustado do índice 1 para 2
                high_price = float(candle[3])  # Ajustado do índice 2 para 3
                low_price = float(candle[4])  # Ajustado do índice 3 para 4
                close_price = float(candle[5])  # Ajustado do índice 4 para 5
            except (IndexError, ValueError) as e:
                logger.error(f"Erro ao converter valores OHLC: {e}")
                return None

            # Criar arrays numpy para os dados OHLC
            opens = np.array([open_price], dtype=np.float64)
            highs = np.array([high_price], dtype=np.float64)
            lows = np.array([low_price], dtype=np.float64)
            closes = np.array([close_price], dtype=np.float64)

            # Itera pelas funções do grupo "Pattern Recognition"
            for nome_funcao in talib.get_function_groups()["Pattern Recognition"]:
                try:
                    funcao_talib = getattr(talib, nome_funcao)
                    resultado_padrao = funcao_talib(opens, highs, lows, closes)

                    if resultado_padrao[0] != 0:
                        nome_padrao = (
                            nome_funcao[3:].lower()
                            if nome_funcao.startswith("CDL")
                            else nome_funcao.lower()
                        )
                        logger.debug(f"Padrão identificado: {nome_padrao}")
                        return nome_padrao

                except Exception as e:
                    logger.error(f"Erro ao processar padrão {nome_funcao}: {e}")
                    continue

            return None

        except (ValueError, IndexError) as e:
            logger.error(f"Erro ao converter dados do candle: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao identificar padrão: {e}")
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
        """Analisa os candles recebidos."""
        try:
            # Valida parâmetros individualmente
            if not self.validador.validar_symbol(symbol):
                return None

            if not self.validador.validar_timeframe(timeframe):
                return None

            if not self.validador.validar_estrutura(dados):
                return None

            # Processa apenas candles válidos
            candles_validos = [
                candle for candle in dados if self.validador.validar_candle(candle)
            ]

            if not candles_validos:
                logger.error("Nenhum candle válido para análise")
                return None

            # Continua processamento...
            return self._executar_analise(candles_validos)

        except Exception as e:
            logger.error(f"Erro na análise de candles: {e}")
            return None

    def _validar_dados_entrada(self, dados):
        """Valida os dados de entrada."""
        return dados and isinstance(dados, (list, tuple))

    def _preparar_dados_numpy(self, dados):
        """Prepara os dados para análise usando numpy."""
        try:
            dados_np = [[float(v) for v in candle[2:]] for candle in dados]
            return np.array(dados_np, dtype=np.float64)
        except Exception as e:
            logger.error(f"Erro ao preparar dados numpy: {e}")
            raise

    def _analisar_padroes_talib(self, dados_np):
        """Analisa padrões usando TA-Lib."""
        resultados = {}
        opens = dados_np[:, 1]
        highs = dados_np[:, 2]
        lows = dados_np[:, 3]
        closes = dados_np[:, 4]

        for nome_funcao in talib.get_function_groups()["Pattern Recognition"]:
            try:
                funcao_talib = getattr(talib, nome_funcao)
                resultado = funcao_talib(opens, highs, lows, closes)
                nome_padrao = nome_funcao.lower().replace("cdl", "")
                resultados[nome_padrao] = resultado
            except Exception as e:
                logger.error(f"Erro no padrão {nome_funcao}: {e}")
                continue

        return resultados

    def _processar_sinais(self, dados, resultados, symbol, timeframe):
        """Processa os sinais identificados."""
        sinais = []
        for candle in dados:
            padrao_candle = self.identificar_padrao(candle)
            if padrao_candle:
                classificacao = self.classificar_candle(candle)
                sinal = self.gerar_sinal(
                    candle, padrao_candle, classificacao, symbol, timeframe, self.config
                )
                if sinal:
                    sinais.append(sinal)
        return sinais

    def _salvar_resultados(self, sinais, symbol, timeframe):
        """Salva os resultados usando o gerenciador de banco."""
        try:
            for sinal in sinais:
                dados = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": sinal.get("timestamp"),
                    "padrao": sinal.get("padrao"),
                    "classificacao": sinal.get("classificacao"),
                    "sinal": sinal.get("sinal"),
                    "stop_loss": sinal.get("stop_loss"),
                    "take_profit": sinal.get("take_profit"),
                }
                gerenciador_banco.inserir_dados("analise_candles", dados)
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}")
