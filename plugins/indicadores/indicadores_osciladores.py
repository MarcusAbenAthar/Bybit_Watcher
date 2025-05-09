# indicadores_osciladores.py

from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger, log_rastreamento
import talib
import numpy as np
from plugins.plugin import Plugin
import logging
from utils.config import carregar_config
from utils.plugin_utils import (
    ajustar_periodos_generico,
    extrair_ohlcv,
    validar_klines,
    calcular_volatilidade_generico,
)

logger = get_logger(__name__)


class IndicadoresOsciladores(Plugin):
    """
    Indicador oscilador.
    Responsabilidade única: cálculo de indicadores osciladores.
    Não deve registrar, inicializar ou finalizar automaticamente.
    Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
    """

    def finalizar(self):
        """
        Finaliza o plugin IndicadoresOsciladores, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.debug("IndicadoresOsciladores finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar IndicadoresOsciladores: {e}")

    """
    Plugin para cálculo de indicadores osciladores.
    - Responsabilidade única: indicadores osciladores.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "indicadores_osciladores"
    PLUGIN_CATEGORIA = "indicador"
    PLUGIN_TAGS = ["indicador", "oscilador", "analise"]
    PLUGIN_PRIORIDADE = 50

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "indicadores_osciladores": {
                "descricao": "Armazena valores dos indicadores osciladores (RSI, Estocástico, MFI, etc.), score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "indicador": "VARCHAR(50) NOT NULL",
                    "valor": "DECIMAL(18,8)",
                    "zona": "VARCHAR(20)",
                    "sinal": "VARCHAR(10)",
                    "forca": "DECIMAL(5,2)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin IndicadoresOsciladores.
        """
        return ["gerenciador_banco", "obter_dados"]

    PLUGIN_NAME = "indicadores_osciladores"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["osciladores", "rsi", "stoch", "mfi"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self.config = config["indicadores"]["osciladores"].copy()

    def calcular_rsi(
        self, klines, symbol: str, timeframe: str, base_periodo=None
    ) -> np.ndarray:
        """
        Calcula o RSI com ajuste dinâmico baseado na volatilidade e config centralizada.
        """
        try:
            close = extrair_ohlcv(klines, [4])[4]
            if close.size < 10:
                return np.array([])
            base_periodo = base_periodo or self.config.get("rsi_periodo", 14)
            volatilidade = calcular_volatilidade_generico(close, periodo=base_periodo)
            ajuste = int(volatilidade * 10)
            if timeframe == "1m":
                base_periodo = max(7, base_periodo // 2)
            elif timeframe == "1d":
                base_periodo = min(28, base_periodo * 2)
            periodo_final = max(7, min(28, base_periodo + ajuste))
            rsi = talib.RSI(close, timeperiod=periodo_final)
            return rsi
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao calcular RSI para {symbol} - {timeframe}: {e}"
            )
            return np.array([])

    def calcular_estocastico(self, klines, timeframe: str) -> tuple:
        """
        Calcula o Estocástico com ajuste dinâmico e config centralizada.
        """
        try:
            extr = extrair_ohlcv(klines, [2, 3, 4])
            high, low, close = extr[2], extr[3], extr[4]
            if len(close) < 10:
                return np.array([]), np.array([])
            vol = calcular_volatilidade_generico(close, periodo=14)
            ajuste = int(vol * 3)
            base = {
                "fastk": self.config.get("estocastico_fastk", 5),
                "slowk": self.config.get("estocastico_slowk", 3),
                "slowd": self.config.get("estocastico_slowd", 3),
            }
            if timeframe == "1m":
                base = {k: max(2, v // 2) for k, v in base.items()}
            elif timeframe == "1d":
                base = {k: min(10, v * 2) for k, v in base.items()}
            fastk = max(3, min(10, base["fastk"] + ajuste))
            slowk = max(2, min(6, base["slowk"] + ajuste))
            slowd = max(2, min(6, base["slowd"] + ajuste))
            slowk_vals, slowd_vals = talib.STOCH(
                high,
                low,
                close,
                fastk_period=fastk,
                slowk_period=slowk,
                slowk_matype=0,
                slowd_period=slowd,
                slowd_matype=0,
            )
            return slowk_vals, slowd_vals
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular Estocástico: {e}")
            return np.array([]), np.array([])

    def calcular_mfi(self, klines, periodo=None) -> np.ndarray:
        """
        Calcula o MFI (Money Flow Index) usando config centralizada.
        """
        try:
            extr = extrair_ohlcv(klines, [2, 3, 4, 5])
            high, low, close, volume = extr[2], extr[3], extr[4], extr[5]
            periodo = periodo or self.config.get("mfi_periodo", 14)
            if len(close) < periodo:
                return np.array([])
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular MFI: {e}")
            return np.array([])

    def executar(self, *args, **kwargs) -> dict:
        """
        Executa o cálculo dos indicadores osciladores.
        Sempre retorna um dicionário de indicadores, nunca bool.
        """
        from utils.logging_config import log_rastreamento

        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"indicadores_osciladores/{symbol}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        resultado_padrao = {
            "osciladores": {
                "rsi": None,
                "estocastico": {"slowk": None, "slowd": None},
                "mfi": None,
                "volatilidade": 0.0,
            }
        }
        try:
            if not validar_klines(dados_completos.get("crus", []), min_len=20):
                return resultado_padrao
            crus = dados_completos.get("crus", [])
            rsi = self.calcular_rsi(crus, symbol, timeframe)
            slowk, slowd = self.calcular_estocastico(crus, timeframe)
            mfi = self.calcular_mfi(crus)
            close = extrair_ohlcv(crus, [4])[4]
            volatilidade = calcular_volatilidade_generico(close, periodo=14)
            resultado = {
                "osciladores": {
                    "rsi": float(rsi[-1]) if rsi.size else None,
                    "estocastico": {
                        "slowk": float(slowk[-1]) if slowk.size else None,
                        "slowd": float(slowd[-1]) if slowd.size else None,
                    },
                    "mfi": float(mfi[-1]) if mfi.size else None,
                    "volatilidade": volatilidade,
                }
            }
            if isinstance(dados_completos, dict):
                dados_completos["osciladores"] = resultado["osciladores"]
            log_rastreamento(
                componente=f"indicadores_osciladores/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"osciladores={resultado}",
            )
            return resultado
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}")
            return resultado_padrao
