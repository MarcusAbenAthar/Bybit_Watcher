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
        try:
            if not candle or len(candle) < 4:
                return None

            abertura, fechamento, maximo, minimo = candle

            # Converte os dados do candle para o formato aceito pelo TA-Lib
            candle_data = {
                "open": abertura,
                "high": maximo,
                "low": minimo,
                "close": fechamento,
            }

            # Identifica o padrão do candle usando a função CDL do TA-Lib
            padrao = None
            for func in talib.get_function_groups()["Pattern Recognition"]:
                result = getattr(talib, func)(candle_data)
                if result != 0:  # Se encontrou um padrão
                    padrao = func.lower().replace("cdl", "")
                    break

            return padrao

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
            dados (list): Lista de candles
            symbol (str): Símbolo do par
            timeframe (str): Timeframe da análise
        """
        try:
            # Implementação da análise
            return self.analisar_candles(dados)
        except Exception as e:
            logger.error(f"Erro ao analisar candles: {e}")
            raise

    def calcular_forca_padrao(self, candle, padrao):
        """
        Calcula a força do padrão identificado.

        Args:
            candle (list): Lista com os dados do candle [open, close, high, low]
            padrao (str): Nome do padrão identificado

        Returns:
            float: Força do padrão (0-100)
        """
        try:
            if not padrao or not candle or len(candle) < 4:
                return 0

            abertura, fechamento, maximo, minimo = candle

            # Calcula o tamanho relativo do candle
            tamanho_corpo = abs(float(fechamento) - float(abertura))
            tamanho_total = float(maximo) - float(minimo)

            # Evita divisão por zero
            if tamanho_total <= 0:
                return 0

            # Calcula a força base pelo tamanho relativo do corpo
            forca_base = (tamanho_corpo / tamanho_total) * 100

            # Ajusta a força baseado no tipo de padrão
            # Verifica se existe o padrão com sufixo _alta ou _baixa
            multiplicador = 1.0
            if f"{padrao}_alta" in PADROES_CANDLES:
                multiplicador = PADROES_CANDLES[f"{padrao}_alta"].get("peso", 1.0)
            elif f"{padrao}_baixa" in PADROES_CANDLES:
                multiplicador = PADROES_CANDLES[f"{padrao}_baixa"].get("peso", 1.0)

            return min(100, forca_base * multiplicador)

        except Exception as e:
            logger.error(f"Erro ao calcular força do padrão: {e}")
            return 0

    def calcular_confianca(self, candle, padrao):
        """
        Calcula a confiança do padrão identificado.

        Args:
            candle (list): Lista com os dados do candle [open, close, high, low]
            padrao (str): Nome do padrão identificado

        Returns:
            float: Confiança do padrão (0-100)
        """
        try:
            if not padrao or not candle or len(candle) < 4:
                return 0

            abertura, fechamento, maximo, minimo = candle

            # Calcula o tamanho relativo do candle
            tamanho_corpo = abs(float(fechamento) - float(abertura))
            tamanho_total = float(maximo) - float(minimo)

            # Evita divisão por zero
            if tamanho_total <= 0:
                return 0

            # Calcula a confiança base pelo tamanho relativo do corpo
            confianca_base = (tamanho_corpo / tamanho_total) * 100

            # Ajusta a confiança baseado no tipo de padrão
            multiplicador = PADROES_CANDLES.get(f"{padrao}_alta", {}).get("peso", 1.0)
            multiplicador = PADROES_CANDLES.get(f"{padrao}_baixa", {}).get(
                "peso", multiplicador
            )

            return min(100, confianca_base * multiplicador)

        except Exception as e:
            logger.error(f"Erro ao calcular confiança do padrão: {e}")
            return 0

    def analisar_candles(self, dados):
        """
        Analisa os padrões nos candles.

        Args:
            dados (list): Lista de candles para análise
        """
        try:
            # Verificar se dados é válido
            if not dados or not isinstance(dados[0], (list, tuple)):
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
            resultados["doji"] = talib.CDLDOJI(opens, highs, lows, closes)
            resultados["hammer"] = talib.CDLHAMMER(opens, highs, lows, closes)

            return resultados

        except Exception as e:
            logger.error(f"Erro na análise de candles: {e}")
            raise
