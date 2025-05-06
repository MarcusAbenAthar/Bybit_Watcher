"""
Plugin de cálculo de risco.
Responsabilidade única: cálculo de risco para operações.
Não deve registrar, inicializar ou finalizar automaticamente.
Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
"""

from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin
from utils.config import carregar_config
from utils.plugin_utils import validar_klines

logger = get_logger(__name__)


class CalculoRisco(Plugin):
    """
    Plugin para cálculo de risco por operação e gerenciamento de exposição.
    - Responsabilidade única: cálculo de risco.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "calculo_risco"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["risco", "gerenciamento", "exposicao"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin CalculoRisco.
        """
        return []

    def __init__(self, **kwargs):
        """
        Inicializa o plugin CalculoRisco.
        """
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("calculo_risco", {}).copy()
            if "plugins" in config and "calculo_risco" in config["plugins"]
            else {}
        )
        self._min_klines = 50
        self._ma_curta = 9
        self._ma_media = 21
        self._ma_longa = 50
        self._rsi_period = 14
        self._atr_period = 14
        self._volume_threshold = 1000

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com configurações fornecidas.

        Args:
            config: Dicionário com configurações (ex.: períodos, thresholds).

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            config_risco = config.get("calculo_risco", {})
            self._min_klines = config_risco.get("min_klines", self._min_klines)
            self._ma_curta = config_risco.get("ma_curta", self._ma_curta)
            self._ma_media = config_risco.get("ma_media", self._ma_media)
            self._ma_longa = config_risco.get("ma_longa", self._ma_longa)
            self._rsi_period = config_risco.get("rsi_period", self._rsi_period)
            self._atr_period = config_risco.get("atr_period", self._atr_period)
            self._volume_threshold = config_risco.get(
                "volume_threshold", self._volume_threshold
            )

            if not all(
                isinstance(p, int) and p > 0
                for p in [
                    self._min_klines,
                    self._ma_curta,
                    self._ma_media,
                    self._ma_longa,
                    self._rsi_period,
                    self._atr_period,
                ]
            ):
                logger.error(f"[{self.nome}] Períodos inválidos")
                return False
            if (
                not isinstance(self._volume_threshold, (int, float))
                or self._volume_threshold <= 0
            ):
                logger.error(
                    f"[{self.nome}] volume_threshold inválido: {self._volume_threshold}"
                )
                return False

            logger.info(
                f"[{self.nome}] inicializado com min_klines={self._min_klines}, "
                f"ma_curta={self._ma_curta}, ma_media={self._ma_media}, "
                f"ma_longa={self._ma_longa}, rsi_period={self._rsi_period}, "
                f"atr_period={self._atr_period}, volume_threshold={self._volume_threshold}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def _validar_klines(self, klines: list, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de klines.

        Args:
            klines: Lista de k-lines.
            symbol: Símbolo do par.
            timeframe: Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(klines, list):
            logger.error(f"[{self.nome}] klines não é uma lista: {type(klines)}")
            return False

        if len(klines) < self._min_klines:
            logger.error(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines, "
                f"requer {self._min_klines}"
            )
            return False

        for kline in klines:
            if not isinstance(kline, (list, tuple)) or len(kline) < 6:
                logger.error(
                    f"[{self.nome}] K-line malformada para {symbol} - {timeframe}: {kline}"
                )
                return False
            try:
                # Verificar se high, low, close, volume são numéricos
                for i in [2, 3, 4, 5]:
                    float(kline[i])
            except (TypeError, ValueError):
                logger.error(
                    f"[{self.nome}] Valor não numérico em k-line para {symbol} - {timeframe}: {kline}"
                )
                return False

        return True

    def executar(self, *args, **kwargs):
        symbol = kwargs.get("symbol", "BTCUSDT")
        timeframe = kwargs.get("timeframe", "1m")
        dados_completos = kwargs.get("dados_completos", {})
        resultado_padrao = {
            "calculo_risco": {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {},
            }
        }
        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            return resultado_padrao
        if not all([symbol, timeframe]):
            logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
            return resultado_padrao
        klines = dados_completos.get("crus", [])
        if not self._validar_klines(klines, symbol, timeframe):
            return resultado_padrao
        try:
            sinal = self.gerar_sinal(klines)
            return {"calculo_risco": sinal}
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return resultado_padrao

    def _extrair_dados(self, dados: list, indices: list) -> dict:
        """
        Extrai dados especificados das k-lines.

        Args:
            dados: Lista de k-lines.
            indices: Lista de índices a extrair (ex.: [2, 3, 4, 5]).

        Returns:
            dict: Dicionário com arrays para cada índice.
        """
        try:
            return {
                i: np.array([float(k[i]) for k in dados], dtype=np.float64)
                for i in indices
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na extração dos dados: {e}")
            return {i: np.array([]) for i in indices}

    def gerar_sinal(self, klines: list) -> dict:
        """
        Gera sinal de risco baseado em indicadores técnicos.

        Args:
            klines: Lista de k-lines.

        Returns:
            dict: Sinal com direção, força, confiança e indicadores.
        """
        try:
            dados_extraidos = self._extrair_dados(klines, [2, 3, 4, 5])
            high = dados_extraidos[2]
            low = dados_extraidos[3]
            close = dados_extraidos[4]
            volume = dados_extraidos[5]

            if len(close) < self._min_klines:
                logger.warning(
                    f"[{self.nome}] Menos de {self._min_klines} candles disponíveis"
                )
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "indicadores": {},
                }

            indicadores = {
                "tendencia": self._confirmar_tendencia(close),
                "volatilidade": self._verificar_volatilidade(high, low, close),
                "momentum": self._calcular_momentum(close),
                "volume": self._verificar_volume(volume),
            }

            # Calcular confiança com pesos dinâmicos
            vol_rel = (
                volume[-1] / np.mean(volume[-10:]) if np.mean(volume[-10:]) > 0 else 1.0
            )
            confianca = (
                (0.4 if indicadores["tendencia"] else 0.0)
                + (0.3 if abs(indicadores["momentum"]) > 0.6 else 0.0)
                + (0.2 if indicadores["volatilidade"] < 0.5 else 0.0)
                + (0.1 * vol_rel)
            )
            confianca = round(min(max(confianca, 0.0), 1.0), 2)

            forca = (
                "FORTE"
                if confianca >= 0.8
                else "MÉDIA" if confianca >= 0.6 else "FRACA"
            )

            momentum = indicadores["momentum"]
            direcao = (
                "ALTA" if momentum > 0.2 else "BAIXA" if momentum < -0.2 else "LATERAL"
            )

            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "indicadores": indicadores,
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao gerar sinal: {e}", exc_info=True)
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {},
            }

    def _confirmar_tendencia(self, close: np.ndarray) -> bool:
        """
        Confirma tendência usando médias móveis e MACD.

        Args:
            close: Array de preços de fechamento.

        Returns:
            bool: True se tendência clara, False caso contrário.
        """
        try:
            ma_curta = talib.SMA(close, timeperiod=self._ma_curta)
            ma_media = talib.SMA(close, timeperiod=self._ma_media)
            ma_longa = talib.SMA(close, timeperiod=self._ma_longa)
            macd, signal, _ = talib.MACD(close)
            tendencia_mas = (
                ma_curta[-1] > ma_media[-1] > ma_longa[-1]
                or ma_curta[-1] < ma_media[-1] < ma_longa[-1]
            )
            tendencia_macd = macd[-1] > signal[-1] or macd[-1] < signal[-1]
            return tendencia_mas and tendencia_macd
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao confirmar tendência: {e}")
            return False

    def _verificar_volatilidade(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray
    ) -> float:
        """
        Calcula volatilidade relativa usando ATR.

        Args:
            high: Array de preços máximos.
            low: Array de preços mínimos.
            close: Array de preços de fechamento.

        Returns:
            float: Volatilidade relativa (ATR/close).
        """
        try:
            atr = talib.ATR(high, low, close, timeperiod=self._atr_period)
            return (
                float(atr[-1]) / float(close[-1]) if atr.size and close[-1] > 0 else 1.0
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao verificar volatilidade: {e}")
            return 1.0

    def _calcular_momentum(self, close: np.ndarray) -> float:
        """
        Calcula momentum usando RSI normalizado.

        Args:
            close: Array de preços de fechamento.

        Returns:
            float: Momentum normalizado (-1.0 a 1.0).
        """
        try:
            rsi = talib.RSI(close, timeperiod=self._rsi_period)
            return (rsi[-1] - 50) / 50 if rsi.size else 0.0
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular momentum: {e}")
            return 0.0

    def _verificar_volume(self, volume: np.ndarray) -> bool:
        """
        Verifica se o volume médio é significativo.

        Args:
            volume: Array de volumes.

        Returns:
            bool: True se volume significativo, False caso contrário.
        """
        try:
            return np.mean(volume[-20:]) >= self._volume_threshold
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao verificar volume: {e}")
            return False

    @property
    def plugin_tabelas(self) -> dict:
        """
        Define as tabelas do plugin conforme padrão institucional (regras de ouro).
        """
        return {
            "calculo_risco": {
                "descricao": "Armazena os cálculos de risco realizados pelo plugin, incluindo direção, força, confiança, indicadores, score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "direcao": "VARCHAR(10)",
                    "forca": "VARCHAR(10)",
                    "confianca": "DECIMAL(5,2)",
                    "indicadores": "JSONB",
                    "risco": "DECIMAL(5,2)",
                    "faixa_entrada_min": "DECIMAL(18,8)",
                    "faixa_entrada_max": "DECIMAL(18,8)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
