from utils.logging_config import get_logger

logger = get_logger(__name__)
import numpy as np
from plugins.gerenciadores import gerenciador_banco
from plugins.validador_dados import ValidadorDados
import talib
from utils.padroes_candles import PADROES_CANDLES

from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin


class AnaliseCandles(Plugin):
    """Plugin para analisar os candles e identificar padrões."""

    PLUGIN_NAME = "analise_candles"
    PLUGIN_TYPE = "adicional"

    def __init__(self, gerente=None, validador=None, calculo_alavancagem=None):
        """
        Inicializa o plugin AnaliseCandles.

        Args:
            gerente: Instância do gerenciador de plugins
            validador: Instância do validador de dados
            calculo_alavancagem: Instância do cálculo de alavancagem
        """
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.descricao = "Plugin para análise de padrões de candles"
        self._config = None
        self.cache_padroes = {}
        self.gerente = gerente
        self._validador = validador
        self._calculo_alavancagem = calculo_alavancagem
        self.inicializado = False

    def inicializar(self, config):
        """Inicializa as dependências do plugin."""
        try:
            if self.inicializado:
                return True

            if not super().inicializar(config):
                return False

            self._config = config

            # Verifica dependências
            if not self._validador:
                logger.error("Validador de dados não fornecido")
                return False

            if not self._validador.inicializado:
                if not self._validador.inicializar(config):
                    logger.error("Falha ao inicializar validador")
                    return False

            if not self._calculo_alavancagem:
                logger.error("Cálculo de alavancagem não fornecido")
                return False

            self.inicializado = True

            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar {self.nome}: {e}")
            return False

    def identificar_padrao(self, dados):
        """Identifica padrões de candlestick nos dados."""
        try:
            if dados is None or len(dados) < 3:
                logger.warning("Dados de candle inválidos: None")
                return None

            dados_np = np.array(dados, dtype=np.float64)
            open_prices = dados_np[:, 1]
            high_prices = dados_np[:, 2]
            low_prices = dados_np[:, 3]
            close_prices = dados_np[:, 4]

            # Chama funções do TALib para identificar padrões
            resultado = talib.CDL2CROWS(
                open_prices, high_prices, low_prices, close_prices
            )

            return resultado[-1] if resultado is not None else None

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

    def gerar_sinal(self, dados, symbol, timeframe):
        """Gera um sinal de trading baseado na análise dos candles."""
        try:
            padrao = self.identificar_padrao(dados)
            if padrao is None:
                return {
                    "sinal": None,
                    "padrao": None,
                    "stop_loss": None,
                    "take_profit": None,
                    "forca": 0.0,
                    "confianca": 0.0,
                }

            forca = self.calcular_forca_padrao(dados)
            confianca = self.calcular_confianca(dados)

            return {
                "sinal": "COMPRA" if padrao > 0 else "VENDA" if padrao < 0 else None,
                "padrao": "CDL2CROWS",
                "stop_loss": self._calcular_stop_loss(dados, padrao),
                "take_profit": self._calcular_take_profit(dados, padrao),
                "forca": forca,
                "confianca": confianca,
            }

        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return None

    def _sinal_padrao(self):
        """Retorna um sinal padrão vazio."""
        return {
            "sinal": None,
            "stop_loss": None,
            "take_profit": None,
            "forca": 0,
            "confianca": 0,
        }

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a análise dos candles.

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
                dados["candles"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                }
                return True

            # Verifica se há dados suficientes
            if not dados or len(dados) < 20:  # Mínimo de candles para análise
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                dados["candles"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                }
                return True

            logger.debug(f"Iniciando análise de candles para {symbol} - {timeframe}")
            resultados = self.analisar_candles(dados, symbol, timeframe)

            if resultados:
                dados["candles"] = resultados
            else:
                dados["candles"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                }

            return True

        except Exception as e:
            logger.error(f"Erro ao analisar candles: {e}")
            dados["candles"] = {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0,
            }
            return True

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

    def calcular_forca_padrao(self, dados):
        """Calcula a força do padrão baseado em volume e movimento de preço."""
        try:
            if dados is None or len(dados) < 3:
                return 0.0

            dados_np = np.array(dados, dtype=np.float64)
            variacao_preco = abs(dados_np[-1, 4] - dados_np[-1, 1]) / dados_np[-1, 1]
            volume_relativo = dados_np[-1, 5] / np.mean(dados_np[:, 5])

            forca = float(variacao_preco * volume_relativo)
            return min(max(forca, 0.0), 1.0)  # Limita entre 0 e 1

        except Exception as e:
            logger.error(f"Erro ao calcular força do padrão: {e}")
            return 0.0

    def calcular_confianca(self, dados):
        """Calcula a confiança do padrão identificado."""
        try:
            if dados is None or len(dados) < 3:
                return 0.0

            dados_np = np.array(dados, dtype=np.float64)
            volatilidade = np.std(
                dados_np[:, 4]
            )  # Desvio padrão dos preços de fechamento
            volume_medio = np.mean(dados_np[:, 5])

            # Normaliza os valores entre 0 e 1
            confianca = float((volatilidade * volume_medio) / (100 * volume_medio))
            return min(max(confianca, 0.0), 1.0)  # Limita entre 0 e 1

        except Exception as e:
            logger.error(f"Erro ao calcular confiança do padrão: {e}")
            return 0.0

    def analisar_candles(self, dados, symbol, timeframe):
        """Analisa os candles recebidos."""
        try:
            if not self.inicializado:
                logger.error("Plugin não inicializado")
                return None

            # Valida parâmetros individualmente
            if not self._validador.validar_symbol(symbol):
                logger.error(f"Symbol inválido: {symbol}")
                return None

            if not self._validador.validar_timeframe(timeframe):
                logger.error(f"Timeframe inválido: {timeframe}")
                return None

            if not self._validador.validar_estrutura(dados):
                logger.error("Estrutura de dados inválida")
                return None

            # Processa apenas candles válidos
            candles_validos = [
                candle for candle in dados if self._validador.validar_candle(candle)
            ]

            if not candles_validos:
                logger.error("Nenhum candle válido para análise")
                return None

            # Analisa os candles
            resultados = self._analisar_padroes_talib(
                self._preparar_dados_numpy(candles_validos)
            )

            # Processa os sinais
            sinais = self._processar_sinais(
                candles_validos, resultados, symbol, timeframe
            )

            # Salva resultados se houver sinais
            if sinais:
                self._salvar_resultados(sinais, symbol, timeframe)

            return {
                "sinais": sinais,
                "resultados": resultados,
                "candles_analisados": len(candles_validos),
            }

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
            return None

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
                    candle,
                    padrao_candle,
                    classificacao,
                    symbol,
                    timeframe,
                    self._config,
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

    def _calcular_stop_loss(self, dados, padrao):
        """Calcula o nível de stop loss baseado no padrão."""
        try:
            dados_np = np.array(dados, dtype=np.float64)
            return (
                float(np.min(dados_np[-3:, 3]))
                if padrao > 0
                else float(np.max(dados_np[-3:, 2]))
            )
        except Exception:
            return None

    def _calcular_take_profit(self, dados, padrao):
        """Calcula o nível de take profit baseado no padrão."""
        try:
            dados_np = np.array(dados, dtype=np.float64)
            return (
                float(np.max(dados_np[-3:, 2]))
                if padrao > 0
                else float(np.min(dados_np[-3:, 3]))
            )
        except Exception:
            return None
