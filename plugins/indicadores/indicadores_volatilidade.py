# indicadores_volatilidade.py
# Plugin para cálculo de indicadores de volatilidade (Bandas de Bollinger, ATR)

from plugins.plugin import Plugin
from utils.logging_config import get_logger, log_rastreamento
import talib
import numpy as np
from utils.config import carregar_config
from utils.plugin_utils import (
    ajustar_periodos_generico,
    extrair_ohlcv,
    validar_klines,
    calcular_volatilidade_generico,
)

logger = get_logger(__name__)


class IndicadoresVolatilidade(Plugin):
    """
    Indicador de volatilidade.
    Responsabilidade única: cálculo de indicadores de volatilidade.
    Não deve registrar, inicializar ou finalizar automaticamente.
    Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
    """

    def finalizar(self):
        """
        Finaliza o plugin IndicadoresVolatilidade, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.debug("IndicadoresVolatilidade finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar IndicadoresVolatilidade: {e}")

    """
    Plugin de indicadores de volatilidade (ex: ATR, Bandas de Bollinger).
    - Responsabilidade única: cálculo de indicadores de volatilidade.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "indicadores_volatilidade"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicadores", "volatilidade", "analise"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin IndicadoresVolatilidade.
        """
        return []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self.config = config["indicadores"]["volatilidade"].copy()
        # Configuração padrão dos períodos
        self.periodos = {
            "bb": 20,  # Período das Bollinger Bands
            "atr": 14,  # Período do ATR
            "volatilidade": 14,  # Período para cálculo da volatilidade
        }
        # Sobrescreve com configuração do arquivo se existir
        if "periodos" in self.config:
            self.periodos.update(self.config["periodos"])

    def executar(self, *args, **kwargs) -> dict:
        """
        Executa o cálculo dos indicadores de volatilidade.
        Sempre retorna um dicionário de indicadores, nunca bool.
        """
        from utils.logging_config import log_rastreamento

        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"indicadores_volatilidade/{symbol}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        resultado_padrao = {
            "volatilidade": {
                "bandas_bollinger": {"superior": None, "media": None, "inferior": None},
                "atr": None,
                "volatilidade": 0.0,
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
            klines = dados_completos.get("crus", [])
            if not validar_klines(klines, min_len=20):
                return resultado_padrao
            close = extrair_ohlcv(klines, [4])[4]
            if close.size == 0:
                return resultado_padrao
            volatilidade_base = calcular_volatilidade_generico(
                close, periodo=self.periodos["volatilidade"]
            )
            # Usa os períodos configurados
            if len(close) < self.periodos["bb"]:
                logger.warning(
                    f"[{self.nome}] Menos de {self.periodos['bb']} candles para Bollinger"
                )
                upper, middle, lower = np.array([]), np.array([]), np.array([])
            else:
                upper, middle, lower = talib.BBANDS(
                    close,
                    timeperiod=self.periodos["bb"],
                    nbdevup=self.config["bb_desvio_padrao"],
                    nbdevdn=self.config["bb_desvio_padrao"],
                    matype=0,
                )
            dados_ohlc = extrair_ohlcv(klines, [2, 3, 4])
            high, low, close_atr = dados_ohlc[2], dados_ohlc[3], dados_ohlc[4]
            atr = talib.ATR(high, low, close_atr, timeperiod=self.periodos["atr"])
            atr_valor = float(atr[-1]) if atr.size > 0 else None
            resultado = {
                "volatilidade": {
                    "bandas_bollinger": {
                        "superior": float(upper[-1]) if upper.size > 0 else None,
                        "media": float(middle[-1]) if middle.size > 0 else None,
                        "inferior": float(lower[-1]) if lower.size > 0 else None,
                    },
                    "atr": atr_valor,
                    "volatilidade": float(volatilidade_base),
                }
            }
            # Alias temporário para retrocompatibilidade
            resultado["volatilidade"]["bb"] = resultado["volatilidade"][
                "bandas_bollinger"
            ]
            if isinstance(dados_completos, dict):
                dados_completos["volatilidade"] = resultado["volatilidade"]
            log_rastreamento(
                componente=f"indicadores_volatilidade/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"volatilidade={resultado}",
            )
            return resultado
        except Exception as e:
            logger.error(
                f"[indicadores_volatilidade] Erro geral ao executar: {e}", exc_info=True
            )
            return resultado_padrao

    @property
    def plugin_tabelas(self) -> dict:
        """
        Define as tabelas do plugin conforme padrão institucional (regras de ouro).
        """
        return {
            "indicadores_volatilidade": {
                "descricao": "Armazena indicadores de volatilidade (Bandas de Bollinger, ATR, etc), faixas, score e contexto.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "bb_superior": "DECIMAL(18,8)",
                    "bb_media": "DECIMAL(18,8)",
                    "bb_inferior": "DECIMAL(18,8)",
                    "atr": "DECIMAL(18,8)",
                    "volatilidade": "DECIMAL(10,6)",
                    "faixa_entrada_min": "DECIMAL(18,8)",
                    "faixa_entrada_max": "DECIMAL(18,8)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
