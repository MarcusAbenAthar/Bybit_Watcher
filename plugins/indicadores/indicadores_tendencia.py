# indicadores_tendencia.py
# Plugin de Indicadores de Tendência

"""
Plugin de Indicadores de Tendência

Este plugin implementa diversos indicadores técnicos para análise de tendência,
incluindo médias móveis, MACD, ADX e outros indicadores direcionais.

Características:
- Análise multi-timeframe
- Confirmações múltiplas
- Níveis de TP/SL automáticos
- Filtros de qualidade
"""

from typing import Dict
import numpy as np
import pandas as pd
from utils.logging_config import get_logger
from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin

logger = get_logger(__name__)


class IndicadoresTendencia(Plugin):
    """
    Plugin para calcular a tendência do token.
    """

    PLUGIN_NAME = "indicadores_tendencia"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerentePlugin, config=None):
        """
        Inicializa o plugin de indicadores de tendência.

        Args:
            gerente: Instância do gerenciador de plugins
            config: Configurações do sistema
        """
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.gerente = gerente
        # Configurações padrão
        self.config = {
            "sma_rapida": 9,
            "sma_lenta": 21,
            "ema_rapida": 12,
            "ema_lenta": 26,
            "macd_signal": 9,
            "adx_periodo": 14,
            "min_adx": 25,
            "min_confianca": 0.8,  # Mínimo de 80% de confiança
        }
        if config:
            self.config.update(config)

    def calcular_medias_moveis(
        self, dados_completos: pd.DataFrame
    ) -> Dict[str, pd.Series]:
        """Calcula diferentes tipos de médias móveis."""
        try:
            close = dados_completos["close"]
            return {
                "sma_rapida": close.rolling(self.config["sma_rapida"]).mean(),
                "sma_lenta": close.rolling(self.config["sma_lenta"]).mean(),
                "ema_rapida": close.ewm(
                    span=self.config["ema_rapida"], adjust=False
                ).mean(),
                "ema_lenta": close.ewm(
                    span=self.config["ema_lenta"], adjust=False
                ).mean(),
            }
        except Exception as e:
            logger.error(f"Erro ao calcular médias móveis: {e}")
            return {
                "sma_rapida": pd.Series(),
                "sma_lenta": pd.Series(),
                "ema_rapida": pd.Series(),
                "ema_lenta": pd.Series(),
            }

    def calcular_macd(self, dados_completos: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calcula o MACD e suas componentes."""
        try:
            close = dados_completos["close"]
            ema_rapida = close.ewm(span=self.config["ema_rapida"], adjust=False).mean()
            ema_lenta = close.ewm(span=self.config["ema_lenta"], adjust=False).mean()
            macd_line = ema_rapida - ema_lenta
            signal_line = macd_line.ewm(
                span=self.config["macd_signal"], adjust=False
            ).mean()
            histogram = macd_line - signal_line
            return {"macd": macd_line, "signal": signal_line, "histogram": histogram}
        except Exception as e:
            logger.error(f"Erro ao calcular MACD: {e}")
            return {
                "macd": pd.Series(),
                "signal": pd.Series(),
                "histogram": pd.Series(),
            }

    def calcular_adx(self, dados_completos: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calcula o ADX (Average Directional Index)."""
        try:
            high = dados_completos["high"]
            low = dados_completos["low"]
            close = dados_completos["close"]
            periodo = self.config["adx_periodo"]

            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({"tr1": tr1, "tr2": tr2, "tr3": tr3}).max(axis=1)
            atr = tr.rolling(periodo).mean()

            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

            pdi = 100 * pd.Series(pos_dm).rolling(periodo).mean() / atr
            ndi = 100 * pd.Series(neg_dm).rolling(periodo).mean() / atr
            dx = 100 * abs(pdi - ndi) / (pdi + ndi)
            adx = dx.rolling(periodo).mean()

            return {"adx": adx, "pdi": pdi, "ndi": ndi}
        except Exception as e:
            logger.error(f"Erro ao calcular ADX: {e}")
            return {"adx": pd.Series(), "pdi": pd.Series(), "ndi": pd.Series()}

    def calcular_atr(self, dados_completos: pd.DataFrame, periodo: int = 14) -> float:
        """Calcula o ATR para definição de TP/SL."""
        try:
            high = dados_completos["high"]
            low = dados_completos["low"]
            close = dados_completos["close"]
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({"tr1": tr1, "tr2": tr2, "tr3": tr3}).max(axis=1)
            return tr.rolling(periodo).mean().iloc[-1]
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return 0

    def gerar_sinal(self, dados_completos: pd.DataFrame) -> Dict[str, any]:
        """
        Gera sinais de trading baseados nos indicadores.

        Args:
            dados_completos: DataFrame com OHLCV

        Returns:
            Dict com sinais e níveis de TP/SL
        """
        resultado_padrao = {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
        try:
            if len(dados_completos) < 20:
                logger.warning("Dados insuficientes para gerar sinal")
                return resultado_padrao

            # Calcula todos os indicadores
            medias = self.calcular_medias_moveis(dados_completos)
            macd = self.calcular_macd(dados_completos)
            adx = self.calcular_adx(dados_completos)

            confirmacoes_compra = 0
            confirmacoes_venda = 0
            total_indicadores = 0

            # 1. Análise de Médias Móveis
            if medias:
                total_indicadores += 1
                if (
                    medias["sma_rapida"].iloc[-1] > medias["sma_lenta"].iloc[-1]
                    and medias["ema_rapida"].iloc[-1] > medias["ema_lenta"].iloc[-1]
                ):
                    confirmacoes_compra += 1
                elif (
                    medias["sma_rapida"].iloc[-1] < medias["sma_lenta"].iloc[-1]
                    and medias["ema_rapida"].iloc[-1] < medias["ema_lenta"].iloc[-1]
                ):
                    confirmacoes_venda += 1

            # 2. Análise MACD
            if macd:
                total_indicadores += 1
                if macd["histogram"].iloc[-1] > 0 and macd["histogram"].iloc[-2] <= 0:
                    confirmacoes_compra += 1
                elif macd["histogram"].iloc[-1] < 0 and macd["histogram"].iloc[-2] >= 0:
                    confirmacoes_venda += 1

            # 3. Análise ADX
            if adx and adx["adx"].iloc[-1] >= self.config["min_adx"]:
                total_indicadores += 1
                if adx["pdi"].iloc[-1] > adx["ndi"].iloc[-1]:
                    confirmacoes_compra += 1
                else:
                    confirmacoes_venda += 1

            if total_indicadores == 0:
                return resultado_padrao

            confianca_compra = confirmacoes_compra / total_indicadores
            confianca_venda = confirmacoes_venda / total_indicadores

            forca = "FRACA"
            if total_indicadores >= 2:
                if confianca_compra >= 0.9 or confianca_venda >= 0.9:
                    forca = "FORTE"
                elif confianca_compra >= 0.8 or confianca_venda >= 0.8:
                    forca = "MÉDIA"

            # Gera sinal com TP/SL
            atr = self.calcular_atr(dados_completos)
            preco_atual = dados_completos["close"].iloc[-1]

            if confianca_compra >= self.config["min_confianca"]:
                stop_loss = preco_atual - (atr * 1.5)
                take_profit = preco_atual + (atr * 2)
                return {
                    "direcao": "ALTA",
                    "forca": forca,
                    "confianca": confianca_compra * 100,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }
            elif confianca_venda >= self.config["min_confianca"]:
                stop_loss = preco_atual + (atr * 1.5)
                take_profit = preco_atual - (atr * 2)
                return {
                    "direcao": "BAIXA",
                    "forca": forca,
                    "confianca": confianca_venda * 100,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }
            return resultado_padrao

        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return resultado_padrao

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(
                    f"Parâmetros necessários não fornecidos - dados_completos: {dados_completos}, symbol: {symbol}, timeframe: {timeframe}"
                )
                return True

            dados_crus = dados_completos.get("crus", [])
            if not isinstance(dados_crus, list) or len(dados_crus) < 20:
                logger.warning(
                    f"Dados insuficientes ou inválidos para {symbol} - {timeframe}"
                )
                dados_completos["processados"]["tendencia"] = resultado_padrao
                return True

            df = pd.DataFrame(
                dados_crus,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            sinal = self.gerar_sinal(df)
            logger.info(f"Sinal gerado para {symbol} - {timeframe}: {sinal}")
            dados_completos["processados"]["tendencia"] = sinal
            return True
        except Exception as e:
            logger.error(f"Erro ao executar análise de tendência: {str(e)}")
            if isinstance(dados_completos, dict) and "processados" in dados_completos:
                dados_completos["processados"]["tendencia"] = resultado_padrao
            return True
