# Plugin para cálculo de indicadores de tendência (SMA, EMA, MACD, ADX, ATR) de forma adaptativa

from typing import Dict
import numpy as np
import talib
from utils.logging_config import get_logger, log_rastreamento
from plugins.plugin import Plugin
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
import logging
from utils.config import carregar_config
from utils.plugin_utils import ajustar_periodos_generico, extrair_ohlcv, validar_klines

logger = get_logger(__name__)


class IndicadoresTendencia(Plugin):
    """
    Indicador de tendência.
    Responsabilidade única: cálculo de indicadores de tendência.
    Não deve registrar, inicializar ou finalizar automaticamente.
    Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
    """

    def finalizar(self):
        """
        Finaliza o plugin IndicadoresTendencia, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.debug("IndicadoresTendencia finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar IndicadoresTendencia: {e}")

    """
    Plugin para cálculo de indicadores de tendência.
    - Responsabilidade única: indicadores de tendência.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "indicadores_tendencia"
    PLUGIN_CATEGORIA = "indicador"
    PLUGIN_TAGS = ["indicador", "tendencia", "analise"]
    PLUGIN_PRIORIDADE = 50

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "indicadores_tendencia": {
                "descricao": "Armazena valores dos indicadores de tendência (SMA, EMA, MACD, ADX, ATR, etc.), score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "indicador": "VARCHAR(50) NOT NULL",
                    "valor": "DECIMAL(18,8)",
                    "direcao": "VARCHAR(10)",
                    "forca": "DECIMAL(5,2)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
            "medias_moveis": {
                "descricao": "Armazena médias móveis calculadas (SMA, EMA, etc.), score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "tipo": "VARCHAR(20) NOT NULL",
                    "periodo": "INTEGER NOT NULL",
                    "valor": "DECIMAL(18,8) NOT NULL",
                    "direcao": "VARCHAR(10)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
        }

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin IndicadoresTendencia.
        """
        return ["gerenciador_banco", "obter_dados"]

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        # Carrega config institucional centralizada
        config = carregar_config()
        self.config = config["indicadores"]["tendencia"].copy()

    def executar(self, *args, **kwargs) -> bool:
        from utils.logging_config import log_rastreamento

        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"indicadores_tendencia/{symbol}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        resultado_padrao = {
            "tendencia": {
                "medias_moveis": {},
                "macd": {},
                "adx": {},
                "atr": 0.0,
            }
        }
        try:
            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                return resultado_padrao
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                return resultado_padrao
            candles = dados_completos.get("crus", [])
            if not validar_klines(candles, min_len=20):
                return resultado_padrao
            ohlc = extrair_ohlcv(candles, [2, 3, 4])
            close = ohlc[4]
            log_rastreamento(
                componente=f"indicadores_tendencia/{symbol}-{timeframe}",
                acao="dados_extraidos",
                detalhes=f"len_close={len(close)}, close_exemplo={close[-5:].tolist() if len(close) >= 5 else close.tolist()}",
            )
            if len(close) < 30:
                return resultado_padrao
            media = np.mean(close[-14:])
            volatilidade = np.std(close[-14:]) / media if media != 0 else 0.0
            periodos = ajustar_periodos_generico(self.config, timeframe, volatilidade)
            sma_r = talib.SMA(close, timeperiod=periodos["sma_rapida"])
            sma_l = talib.SMA(close, timeperiod=periodos["sma_lenta"])
            ema_r = talib.EMA(close, timeperiod=periodos["ema_rapida"])
            ema_l = talib.EMA(close, timeperiod=periodos["ema_lenta"])
            macd, signal, hist = talib.MACD(
                close,
                fastperiod=periodos["ema_rapida"],
                slowperiod=periodos["ema_lenta"],
                signalperiod=periodos["macd_signal"],
            )
            adx = talib.ADX(ohlc[2], ohlc[3], close, timeperiod=periodos["adx_periodo"])
            pdi = talib.PLUS_DI(
                ohlc[2], ohlc[3], close, timeperiod=periodos["adx_periodo"]
            )
            ndi = talib.MINUS_DI(
                ohlc[2], ohlc[3], close, timeperiod=periodos["adx_periodo"]
            )
            atr = talib.ATR(ohlc[2], ohlc[3], close, timeperiod=periodos["atr_periodo"])
            log_rastreamento(
                componente=f"indicadores_tendencia/{symbol}-{timeframe}",
                acao="indicadores_calculados",
                detalhes=(
                    f"sma_r={sma_r[-1] if sma_r.size else None}, "
                    f"sma_l={sma_l[-1] if sma_l.size else None}, "
                    f"ema_r={ema_r[-1] if ema_r.size else None}, "
                    f"ema_l={ema_l[-1] if ema_l.size else None}, "
                    f"macd={macd[-1] if macd.size else None}, "
                    f"signal={signal[-1] if signal.size else None}, "
                    f"hist={hist[-1] if hist.size else None}, "
                    f"adx={adx[-1] if adx.size else None}, "
                    f"pdi={pdi[-1] if pdi.size else None}, "
                    f"ndi={ndi[-1] if ndi.size else None}, "
                    f"atr={atr[-1] if atr.size else None}"
                ),
            )
            tendencia = {
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
            if isinstance(dados_completos, dict):
                dados_completos["tendencia"] = tendencia
                dados_completos["atr"] = tendencia["atr"]
                dados_completos["preco_atual"] = (
                    float(close[-1]) if len(close) > 0 else 0.0
                )
                if "suporte" in dados_completos:
                    dados_completos["suporte"] = dados_completos["suporte"]
                if "resistencia" in dados_completos:
                    dados_completos["resistencia"] = dados_completos["resistencia"]
            log_rastreamento(
                componente=f"indicadores_tendencia/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"tendencia={tendencia}",
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}")
            return resultado_padrao
