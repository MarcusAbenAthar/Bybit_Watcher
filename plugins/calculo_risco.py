# calculo_risco.py
# Plugin para cálculos de risco e análise de sinais

from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class CalculoRisco(Plugin):
    """Plugin para cálculos de risco."""

    # Identificador explícito do plugin
    PLUGIN_NAME = "calculo_risco"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o plugin CalculoRisco."""
        super().__init__()
        self.nome = "calculo_risco"
        self.descricao = "Plugin para análise e cálculo de risco"
        self._config = None
        self.cache_risco = {}  # Cache para otimização
        self._validador = None  # Instância do validador de dados

    def inicializar(self, config):
        """Inicializa as dependências do plugin."""
        if not self._config:  # Só inicializa uma vez
            super().inicializar(config)
            self._config = config
            if not self._validador:
                logger.error(f"Plugin {self.nome} requer validador_dados")
                return False

            return True
        return True

    def sinal_confiavel(self, sinal):
        """Verifica se o sinal atende aos critérios de confiabilidade."""
        try:
            criterios = {
                "confianca_minima": 0.8,  # 80% de confiança
                "forca_minima": "MEDIA",  # Força mínima necessária
                "volume_minimo": 1000,  # Volume mínimo de negociação
                "tendencia_confirmada": True,  # Confirmação por múltiplos timeframes
                "volatilidade_maxima": 0.8,  # Volatilidade máxima aceitável
                "momentum_minimo": 0.6,  # Momentum mínimo necessário
            }

            # Mapa de força para comparação numérica
            forca_map = {"FRACA": 0, "MEDIA": 1, "FORTE": 2}

            if (
                sinal["confianca"] >= criterios["confianca_minima"]
                and forca_map[sinal["forca"]] >= forca_map[criterios["forca_minima"]]
                and self.verificar_volume(criterios["volume_minimo"])
                and self.confirmar_tendencia()
                and self.verificar_volatilidade() <= criterios["volatilidade_maxima"]
                and abs(self.calcular_momentum()) >= criterios["momentum_minimo"]
            ):
                logger.debug(f"Sinal atendeu todos os critérios: {sinal}")
                return True

            logger.debug(f"Sinal não atendeu critérios: {sinal}")
            return False

        except Exception as e:
            logger.error(f"Erro ao verificar confiabilidade do sinal: {e}")
            return False

    def verificar_volume(self, volume_minimo):
        """Verifica se o volume de negociação é adequado."""
        try:
            volume_medio = np.mean([float(candle[5]) for candle in self.dados[-20:]])
            return volume_medio >= volume_minimo
        except Exception as e:
            logger.error(f"Erro ao verificar volume: {e}")
            return False

    def confirmar_tendencia(self):
        """Confirma tendência usando múltiplos indicadores."""
        try:
            closes = np.array([float(candle[4]) for candle in self.dados])

            # Médias móveis
            ma_curta = talib.SMA(closes, timeperiod=9)
            ma_media = talib.SMA(closes, timeperiod=21)
            ma_longa = talib.SMA(closes, timeperiod=50)

            # MACD
            macd, signal, _ = talib.MACD(closes)

            # Tendência confirmada se:
            # - MAs alinhadas corretamente
            # - MACD consistente com direção
            tendencia_mas = (
                ma_curta[-1] > ma_media[-1] > ma_longa[-1]  # Tendência de alta
                or ma_curta[-1] < ma_media[-1] < ma_longa[-1]  # Tendência de baixa
            )

            tendencia_macd = (
                macd[-1] > signal[-1]  # MACD confirmando alta
                or macd[-1] < signal[-1]  # MACD confirmando baixa
            )

            return tendencia_mas and tendencia_macd

        except Exception as e:
            logger.error(f"Erro ao confirmar tendência: {e}")
            return False

    def verificar_volatilidade(self):
        """Calcula e verifica nível de volatilidade."""
        try:
            # Extrai high, low e close dos candles
            high = np.array([float(candle[2]) for candle in self.dados])
            low = np.array([float(candle[3]) for candle in self.dados])
            closes = np.array([float(candle[4]) for candle in self.dados])

            return talib.ATR(high, low, closes, timeperiod=14)[-1]
        except Exception as e:
            logger.error(f"Erro ao verificar volatilidade: {e}")
            return 1.0  # Retorna volatilidade alta em caso de erro

    def calcular_momentum(self):
        """Calcula força do momentum atual."""
        try:
            closes = np.array([float(candle[4]) for candle in self.dados])
            rsi = talib.RSI(closes, timeperiod=14)
            return (rsi[-1] - 50) / 50  # Normalizado entre -1 e 1
        except Exception as e:
            logger.error(f"Erro ao calcular momentum: {e}")
            return 0

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa análise de risco e gera sinais.

        Args:
            *args: Argumentos posicionais ignorados
            **kwargs: Argumentos nomeados contendo:
                dados (list): Lista de candles
                symbol (str): Par de trading
                timeframe (str): Timeframe atual
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
                dados["calculo_risco"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                    "indicadores": {},
                }
                return True

            self.dados = dados

            # Verifica se há dados suficientes e válidos
            if (
                len(dados) < 50
                or np.isnan(np.array([float(candle[4]) for candle in dados])).any()
            ):
                logger.debug(
                    f"Dados insuficientes ou inválidos para {symbol} - {timeframe}"
                )
                dados["calculo_risco"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                    "indicadores": {},
                }
                return True

            sinal = {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {
                    "tendencia": self.confirmar_tendencia(),
                    "volatilidade": self.verificar_volatilidade(),
                    "momentum": self.calcular_momentum(),
                },
            }

            # Atualiza confiança baseado nos indicadores
            if sinal["indicadores"]["tendencia"]:
                sinal["confianca"] += 0.4

            if abs(sinal["indicadores"]["momentum"]) > 0.6:
                sinal["confianca"] += 0.3

            if sinal["indicadores"]["volatilidade"] < 0.5:
                sinal["confianca"] += 0.3

            # Determina força do sinal
            if sinal["confianca"] >= 0.8:
                sinal["forca"] = "FORTE"
            elif sinal["confianca"] >= 0.6:
                sinal["forca"] = "MEDIA"

            # Determina direção
            momentum = sinal["indicadores"]["momentum"]
            if momentum > 0.2:
                sinal["direcao"] = "COMPRA"
            elif momentum < -0.2:
                sinal["direcao"] = "VENDA"

            # Só loga se for confiável E tiver direção definida
            if (
                self.sinal_confiavel(sinal)
                and sinal["direcao"] != "NEUTRO"
                and sinal["forca"] != "FRACA"
                and sinal["confianca"] > 0.0
            ):

                logger.info(
                    f"SINAL CONFIÁVEL DETECTADO:\n"
                    f"Symbol: {symbol}\n"
                    f"Timeframe: {timeframe}\n"
                    f"Direção: {sinal['direcao']}\n"
                    f"Força: {sinal['forca']}\n"
                    f"Confiança: {sinal['confianca']:.2f}\n"
                    f"Indicadores: {sinal['indicadores']}"
                )
            else:
                logger.debug(
                    f"Sinal descartado para {symbol} - {timeframe} (não atende critérios)"
                )

            # Atualiza o dicionário de dados com o sinal
            dados["calculo_risco"] = sinal
            return True

        except Exception as e:
            logger.error(f"Erro na execução do cálculo de risco: {e}")
            dados["calculo_risco"] = {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0,
                "indicadores": {},
            }
            return True
