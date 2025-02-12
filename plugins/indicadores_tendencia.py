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

from typing import List, Tuple, Dict, Optional
import numpy as np
import pandas as pd
from utils.logging_config import get_logger

logger = get_logger(__name__)


from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import obter_banco_dados


class IndicadoresTendencia(Plugin):
    def __init__(self, config=None):
        """Inicializa o plugin de indicadores de tendência."""
        super().__init__()
        self.nome = "Indicadores de Tendência"
        self.config = config

    def calcular_medias_moveis(self, dados: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calcula diferentes tipos de médias móveis.

        Args:
            dados: DataFrame com OHLCV

        Returns:
            Dict com as diferentes médias móveis calculadas
        """
        try:
            close = dados["close"]

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
            return {}

    def calcular_macd(self, dados: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calcula o MACD e suas componentes.

        Args:
            dados: DataFrame com OHLCV

        Returns:
            Dict com linha MACD, signal e histograma
        """
        try:
            close = dados["close"]
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
            return {}

    def calcular_adx(self, dados: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calcula o ADX (Average Directional Index).

        Args:
            dados: DataFrame com OHLCV

        Returns:
            Dict com ADX e indicadores direcionais
        """
        try:
            high = dados["high"]
            low = dados["low"]
            close = dados["close"]
            periodo = self.config["adx_periodo"]

            # Cálculo do True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({"tr1": tr1, "tr2": tr2, "tr3": tr3}).max(axis=1)
            atr = tr.rolling(periodo).mean()

            # Movimento Direcional
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
            return {}

    def gerar_sinal(self, dados: pd.DataFrame) -> Dict[str, any]:
        """
        Gera sinais de trading baseados nos indicadores.

        Args:
            dados: DataFrame com OHLCV

        Returns:
            Dict com sinais e níveis de TP/SL
        """
        try:
            # Calcula todos os indicadores
            medias = self.calcular_medias_moveis(dados)
            macd = self.calcular_macd(dados)
            adx = self.calcular_adx(dados)

            # Inicializa contadores de confirmação
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

            # Calcula níveis de confiança
            if total_indicadores > 0:
                confianca_compra = confirmacoes_compra / total_indicadores
                confianca_venda = confirmacoes_venda / total_indicadores
            else:
                return {"sinal": "NEUTRO", "confianca": 0}

            # Determina força do sinal
            forca = "FRACA"
            if total_indicadores >= 2:
                if confianca_compra >= 0.8 or confianca_venda >= 0.8:
                    forca = "FORTE"
                elif confianca_compra >= 0.6 or confianca_venda >= 0.6:
                    forca = "MÉDIA"

            # Gera sinal final com base na confiança mínima
            if confianca_compra >= self.config["min_confianca"]:
                # Calcula níveis de TP/SL para compra
                atr = self.calcular_atr(dados)
                preco_atual = dados["close"].iloc[-1]
                stop_loss = preco_atual - (atr * 1.5)
                take_profit = preco_atual + (atr * 2)

                return {
                    "direcao": "ALTA",
                    "forca": forca,
                    "confianca": confianca_compra * 100,  # Converte para percentual
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }

            elif confianca_venda >= self.config["min_confianca"]:
                # Calcula níveis de TP/SL para venda
                atr = self.calcular_atr(dados)
                preco_atual = dados["close"].iloc[-1]
                stop_loss = preco_atual + (atr * 1.5)
                take_profit = preco_atual - (atr * 2)

                return {
                    "direcao": "BAIXA",
                    "forca": forca,
                    "confianca": confianca_venda * 100,  # Converte para percentual
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }

            return {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0}

        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {"sinal": "ERRO", "confianca": 0}

    def calcular_atr(self, dados: pd.DataFrame, periodo: int = 14) -> float:
        """Calcula o ATR para definição de TP/SL."""
        try:
            high = dados["high"]
            low = dados["low"]
            close = dados["close"]

            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({"tr1": tr1, "tr2": tr2, "tr3": tr3}).max(axis=1)
            atr = tr.rolling(periodo).mean().iloc[-1]

            return atr
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return 0

    def executar(self, dados: List[Tuple], symbol: str, timeframe: str, config) -> None:
        """
        Executa a análise de tendência e salva os resultados.

        Args:
            dados: Lista de tuplas com dados OHLCV
            symbol: Símbolo do par
            timeframe: Timeframe da análise
            config: Configurações do bot
        """
        try:
            # Obtém o banco de dados quando necessário
            banco_dados = obter_banco_dados(config)

            logger.debug(f"Iniciando análise de tendência para {symbol} - {timeframe}")
            logger.debug(f"Quantidade de dados recebidos: {len(dados)}")

            # Converte dados para DataFrame
            df = pd.DataFrame(
                dados,
                columns=[
                    "symbol",
                    "timeframe",
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ],
            )

            logger.debug(f"DataFrame criado com sucesso. Shape: {df.shape}")

            # Atualiza configurações se necessário
            if config.has_section("indicadores_tendencia"):
                self.config.update(config["indicadores_tendencia"])
                logger.debug("Configurações atualizadas")

            # Gera sinal
            sinal = self.gerar_sinal(df)
            logger.debug(f"Sinal gerado: {sinal}")

            # Loga resultado
            if sinal["direcao"] != "NEUTRO":
                logger.info(
                    f"{symbol} - {timeframe} - Direção: {sinal['direcao']} "
                    f"(Força: {sinal['forca']}, Confiança: {sinal['confianca']:.2f}%)"
                )

                if "stop_loss" in sinal:
                    logger.info(
                        f"Stop Loss: {sinal['stop_loss']:.8f} | "
                        f"Take Profit: {sinal['take_profit']:.8f}"
                    )

            # Salva resultado no banco de dados
            banco_dados.salvar_sinal(
                symbol=symbol,
                timeframe=timeframe,
                tipo="tendencia",
                sinal=sinal["direcao"],
                forca=sinal["forca"],
                confianca=sinal["confianca"],
                stop_loss=sinal.get("stop_loss"),
                take_profit=sinal.get("take_profit"),
                timestamp=df["timestamp"].iloc[-1],
            )
            logger.debug("Sinal salvo no banco de dados")

        except Exception as e:
            logger.error(f"Erro ao executar análise de tendência: {e}")
            logger.exception("Detalhes do erro:")
