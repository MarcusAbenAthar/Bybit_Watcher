from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class MediasMoveis(Plugin):
    """Plugin para cálculo e análise de médias móveis."""

    PLUGIN_NAME = "medias_moveis"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o plugin MediasMoveis."""
        super().__init__()
        self.nome = "medias_moveis"
        self.descricao = "Plugin para análise de médias móveis"
        self._config = None
        self.cache_medias = {}

    def inicializar(self, config):
        """
        Inicializa o plugin com as configurações fornecidas.

        Args:
            config: Objeto de configuração
        """
        if not self._config:  # Só inicializa uma vez
            super().inicializar(config)
            self._config = config
            self.cache_medias = {}
            return True
        return True

    def calcular_media_movel(self, dados, periodo, tipo="simples"):
        """
        Calcula a média móvel dos preços.

        Args:
            dados: numpy.ndarray com dados OHLCV
            periodo: int com o período da média
            tipo: str indicando o tipo de média ("simples", "exponencial", "ponderada")

        Returns:
            numpy.ndarray com os valores da média móvel

        Raises:
            ValueError: se o tipo de média for inválido
        """
        try:
            dados_np = np.array(dados)
            fechamentos = dados_np[:, 4].astype(np.float64)  # Coluna de fechamento

            if tipo == "simples":
                return talib.SMA(fechamentos, timeperiod=periodo)
            elif tipo == "exponencial":
                return talib.EMA(fechamentos, timeperiod=periodo)
            elif tipo == "ponderada":
                return talib.WMA(fechamentos, timeperiod=periodo)
            else:
                raise ValueError(f"Tipo de média móvel inválido: {tipo}")

        except ValueError as e:
            logger.error(f"Erro ao calcular média móvel: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao calcular média móvel: {e}")
            return None

    def gerar_sinal(self, dados, padrao, symbol, timeframe, config):
        """
        Gera sinais baseados em médias móveis.

        Args:
            dados: numpy array com dados OHLCV
            padrao: tipo de padrão a ser analisado
            symbol: par de trading
            timeframe: período temporal
            config: configurações

        Returns:
            dict: Dicionário com o sinal gerado
        """
        try:
            periodo_curto = config.getint("medias_moveis", "periodo_curto", fallback=9)
            periodo_longo = config.getint("medias_moveis", "periodo_longo", fallback=21)

            media_movel_curta = self.calcular_media_movel(
                dados, periodo_curto, "exponencial"
            )
            media_movel_longa = self.calcular_media_movel(
                dados, periodo_longo, "exponencial"
            )

            if len(media_movel_curta) < 2 or len(media_movel_longa) < 2:
                return {
                    "sinal": None,
                    "tipo": "medias_moveis",
                    "padrao": padrao,
                    "indicadores": {"media_curta": None, "media_longa": None},
                }

            sinal = None
            if padrao == "cruzamento_alta":
                if (
                    media_movel_curta[-2] < media_movel_longa[-2]
                    and media_movel_curta[-1] > media_movel_longa[-1]
                ):
                    sinal = "COMPRA"
            elif padrao == "cruzamento_baixa":
                if (
                    media_movel_curta[-2] > media_movel_longa[-2]
                    and media_movel_curta[-1] < media_movel_longa[-1]
                ):
                    sinal = "VENDA"

            return {
                "sinal": sinal,
                "tipo": "medias_moveis",
                "padrao": padrao,
                "indicadores": {
                    "media_curta": (
                        media_movel_curta[-1] if len(media_movel_curta) > 0 else None
                    ),
                    "media_longa": (
                        media_movel_longa[-1] if len(media_movel_longa) > 0 else None
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Erro ao gerar sinal de médias móveis: {e}")
            return {"sinal": None, "tipo": "medias_moveis", "padrao": padrao}

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a análise de médias móveis.

        Args:
            *args: Argumentos posicionais ignorados
            **kwargs: Argumentos nomeados contendo:
                dados_completos (dict): Dicionário com dados crus e processados
                symbol (str): Símbolo do par
                timeframe (str): Timeframe
                config (dict): Configurações

        Returns:
            bool: True se executado com sucesso
        """
        try:
            # Extrai os parâmetros necessários
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            config = kwargs.get("config", {})

            # Validação dos parâmetros
            if not all([dados_completos, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                return False

            if "crus" not in dados_completos or not dados_completos["crus"]:
                logger.warning("Dados brutos não disponíveis")
                dados_completos["processados"]["medias_moveis"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                    "indicadores": {
                        "ma20": None,
                        "ma50": None,
                        "distancia": 0,
                        "alavancagem": 1,
                    },
                }
                return True

            dados = dados_completos["crus"]
            if len(dados) < 20:  # Mínimo de candles para análise
                logger.warning("Dados insuficientes para análise")
                dados_completos["processados"]["medias_moveis"] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                    "indicadores": {
                        "ma20": None,
                        "ma50": None,
                        "distancia": 0,
                        "alavancagem": 1,
                    },
                }
                return True

            # Inicializa alavancagem com valor padrão
            self.alavancagem = 1

            # Calcular médias móveis
            closes = np.array([float(candle[4]) for candle in dados])
            ma20 = talib.SMA(closes, timeperiod=20)
            ma50 = talib.SMA(closes, timeperiod=50)

            # Calcular alavancagem baseada na volatilidade
            self.alavancagem = self._calcular_alavancagem(closes)

            # Calcula distância percentual entre médias
            distancia = abs(ma20[-1] - ma50[-1]) / ma50[-1] * 100

            # Determina força do sinal baseada na distância
            if distancia >= 2.0:
                forca = "FORTE"
            elif distancia >= 1.0:
                forca = "MÉDIA"
            else:
                forca = "FRACA"

            # Calcula consistência do movimento (últimos 5 períodos)
            tendencia_alta = sum(1 for i in range(-5, 0) if ma20[i] > ma50[i])
            tendencia_baixa = sum(1 for i in range(-5, 0) if ma20[i] < ma50[i])

            # Calcula confiança baseada na consistência
            if tendencia_alta > tendencia_baixa:
                confianca = (tendencia_alta / 5) * 100
                direcao = "ALTA"
            elif tendencia_baixa > tendencia_alta:
                confianca = (tendencia_baixa / 5) * 100
                direcao = "BAIXA"
            else:
                confianca = 0
                direcao = "NEUTRO"

            # Gera sinal no formato padrão
            sinal = {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "indicadores": {
                    "ma20": float(ma20[-1]),
                    "ma50": float(ma50[-1]),
                    "distancia": distancia,
                    "alavancagem": self.alavancagem,
                },
            }

            # Armazena o resultado em dados_completos["processados"]
            if "processados" not in dados_completos:
                dados_completos["processados"] = {}
            dados_completos["processados"]["medias_moveis"] = sinal
            logger.info(f"Médias móveis calculadas para {symbol} ({timeframe})")
            return True

        except Exception as e:
            logger.error(f"Erro ao processar médias móveis: {e}")
            if "processados" not in dados_completos:
                dados_completos["processados"] = {}
            dados_completos["processados"]["medias_moveis"] = {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0,
                "indicadores": {
                    "ma20": None,
                    "ma50": None,
                    "distancia": 0,
                    "alavancagem": 1,
                },
            }
            return True

    def _calcular_alavancagem(self, closes):
        """
        Calcula a alavancagem baseada na volatilidade.
        """
        try:
            volatilidade = np.std(closes[-20:]) / np.mean(closes[-20:])
            alavancagem = max(1, min(20, int(1 / volatilidade)))
            return alavancagem
        except Exception as e:
            logger.error(f"Erro ao calcular alavancagem: {e}")
            return 1
