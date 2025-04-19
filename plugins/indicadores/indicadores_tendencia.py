# Plugin para cálculo de indicadores de tendência (SMA, EMA, MACD, ADX, ATR) de forma adaptativa

from typing import Dict
import numpy as np
import talib
from utils.logging_config import get_logger
from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins

logger = get_logger(__name__)


class IndicadoresTendencia(Plugin):
    PLUGIN_NAME = "indicadores_tendencia"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicador", "tendencia"]

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente

    def _validar_candles(self, candles, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de candles.

        Args:
            candles: Lista de k-lines.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(candles, list):
            logger.error(f"[{self.nome}] candles não é uma lista: {type(candles)}")
            return False

        if len(candles) < 30:
            logger.warning(
                f"[{self.nome}] Candles insuficientes para {symbol} - {timeframe}"
            )
            return False

        for item in candles:
            if not isinstance(item, (list, tuple)) or len(item) < 5:
                logger.error(
                    f"[{self.nome}] Item inválido em candles para {symbol} - {timeframe}: {item}"
                )
                return False
            # Verificar se os elementos necessários são numéricos
            for idx in [2, 3, 4]:  # high, low, close
                if not isinstance(item[idx], (int, float)):
                    try:
                        float(item[idx])
                    except (TypeError, ValueError):
                        logger.error(
                            f"[{self.nome}] Valor não numérico em candles[{idx}]: {item[idx]}"
                        )
                        return False

        return True

    def _ajustar_periodos(self, timeframe: str, volatilidade: float) -> dict:
        """
        Ajusta períodos dos indicadores com base em timeframe e volatilidade.

        Args:
            timeframe (str): Timeframe (ex.: '1m', '1d').
            volatilidade (float): Volatilidade calculada.

        Returns:
            dict: Períodos ajustados para indicadores.
        """
        multiplicador = 1.0
        if timeframe == "1m":
            multiplicador = 0.5
        elif timeframe == "1d":
            multiplicador = 1.5
        multiplicador += min(max(volatilidade * 2, -0.5), 1.0)

        return {
            "sma_rapida": int(max(5, 9 * multiplicador)),
            "sma_lenta": int(max(10, 21 * multiplicador)),
            "ema_rapida": int(max(5, 12 * multiplicador)),
            "ema_lenta": int(max(10, 26 * multiplicador)),
            "macd_signal": 9,
            "adx_periodo": int(max(5, 14 * multiplicador)),
            "atr_periodo": int(max(5, 14 * multiplicador)),
        }

    def _extrair_ohlcv(self, dados) -> dict:
        """
        Extrai OHLC de candles com validação de tipos.

        Args:
            dados: Lista de k-lines.

        Returns:
            dict: Arrays com high, low, close.
        """
        try:
            high = []
            low = []
            close = []
            for d in dados:
                # Validar tipos antes da conversão
                for idx, field in [(2, "high"), (3, "low"), (4, "close")]:
                    if not isinstance(d[idx], (int, float)):
                        try:
                            float(d[idx])
                        except (TypeError, ValueError):
                            logger.error(
                                f"[{self.nome}] Valor inválido para {field}: {d[idx]}"
                            )
                            return {
                                "high": np.array([]),
                                "low": np.array([]),
                                "close": np.array([]),
                            }
                high.append(float(d[2]))
                low.append(float(d[3]))
                close.append(float(d[4]))
            return {
                "high": np.array(high),
                "low": np.array(low),
                "close": np.array(close),
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair OHLC: {e}")
            return {"high": np.array([]), "low": np.array([]), "close": np.array([])}

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo dos indicadores de tendência e armazena resultados.

        Args:
            dados_completos (dict): Dicionário com dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em caso de erro, para não interromper o pipeline).
        """
        resultado_padrao = {
            "medias_moveis": {},
            "macd": {},
            "adx": {},
            "atr": 0.0,
        }

        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                if isinstance(dados_completos, dict):
                    dados_completos["tendencia"] = resultado_padrao
                return True

            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                dados_completos["tendencia"] = resultado_padrao
                return True

            candles = dados_completos.get("crus", [])
            if not self._validar_candles(candles, symbol, timeframe):
                dados_completos["tendencia"] = resultado_padrao
                return True

            ohlc = self._extrair_ohlcv(candles)
            close = ohlc["close"]
            if len(close) < 30:
                dados_completos["tendencia"] = resultado_padrao
                return True

            media = np.mean(close[-14:])
            volatilidade = np.std(close[-14:]) / media if media != 0 else 0.0

            periodos = self._ajustar_periodos(timeframe, volatilidade)

            # Médias móveis
            sma_r = talib.SMA(close, timeperiod=periodos["sma_rapida"])
            sma_l = talib.SMA(close, timeperiod=periodos["sma_lenta"])
            ema_r = talib.EMA(close, timeperiod=periodos["ema_rapida"])
            ema_l = talib.EMA(close, timeperiod=periodos["ema_lenta"])

            # MACD
            macd, signal, hist = talib.MACD(
                close,
                fastperiod=periodos["ema_rapida"],
                slowperiod=periodos["ema_lenta"],
                signalperiod=periodos["macd_signal"],
            )

            # ADX
            adx = talib.ADX(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["adx_periodo"]
            )
            pdi = talib.PLUS_DI(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["adx_periodo"]
            )
            ndi = talib.MINUS_DI(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["adx_periodo"]
            )

            # ATR
            atr = talib.ATR(
                ohlc["high"], ohlc["low"], close, timeperiod=periodos["atr_periodo"]
            )

            dados_completos["tendencia"] = {
                "medias_moveis": {
                    "sma_rapida": float(sma_r[-1]) if sma_r.size else None,
                    "sma_lenta": float(sma_l[-1]) if sma_l.size else None,
                    "ema_rapida": float(ema_r[-1]) if ema_r.size else None,
                    "ema_lenta": float(ema_l[-1]) if ema_l.size else None,
                },
                "macd": {
                    "macd": float(macd[-1]) if macd.size else None,
                    "signal": float(signal[-1]) if signal.size else None,
                    "histogram": float(hist[-1]) if hist.size else None,
                },
                "adx": {
                    "adx": float(adx[-1]) if adx.size else None,
                    "pdi": float(pdi[-1]) if pdi.size else None,
                    "ndi": float(ndi[-1]) if ndi.size else None,
                },
                "atr": float(atr[-1]) if atr.size else 0.0,
            }
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["tendencia"] = resultado_padrao
            return True
