# indicadores_osciladores.py

from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresOsciladores(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin IndicadoresOsciladores, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("IndicadoresOsciladores finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar IndicadoresOsciladores: {e}")

    """
    Plugin de indicadores osciladores (ex: RSI, Estocástico).
    - Responsabilidade única: cálculo de indicadores osciladores.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "indicadores_osciladores"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["indicadores", "osciladores", "analise"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin IndicadoresOsciladores.
        """
        return []

    PLUGIN_NAME = "indicadores_osciladores"
    PLUGIN_TYPE = "indicador"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["osciladores", "rsi", "stoch", "mfi"]

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente

    def _validar_dados_completos(
        self, dados_completos: dict, symbol: str, timeframe: str
    ) -> bool:
        """
        Valida o formato de dados_completos e crus.

        Args:
            dados_completos: Dicionário com dados a serem validados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            return False

        crus = dados_completos.get("crus")
        if not isinstance(crus, list):
            logger.error(f"[{self.nome}] crus não é uma lista: {type(crus)}")
            return False

        if len(crus) < 20:
            logger.warning(
                f"[{self.nome}] Dados crus insuficientes para {symbol} - {timeframe}"
            )
            return False

        for item in crus:
            if not isinstance(item, (list, tuple)) or len(item) < 6:
                logger.error(
                    f"[{self.nome}] Item inválido em crus para {symbol} - {timeframe}: {item}"
                )
                return False

        return True

    def calcular_rsi(
        self, klines, symbol: str, timeframe: str, base_periodo=14
    ) -> np.ndarray:
        """
        Calcula o RSI com ajuste dinâmico baseado na volatilidade.

        Args:
            klines: Lista de k-lines.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.
            base_periodo (int): Período base para RSI.

        Returns:
            np.ndarray: Valores do RSI ou array vazio em caso de erro.
        """
        try:
            close = self._extrair_dados(klines, [4])[4]
            if close.size < 10:
                return np.array([])

            volatilidade = self._calcular_volatilidade(close)
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
        Calcula o Estocástico com ajuste dinâmico.

        Args:
            klines: Lista de k-lines.
            timeframe (str): Timeframe.

        Returns:
            tuple: (slowk, slowd) ou (array vazio, array vazio) em caso de erro.
        """
        try:
            extr = self._extrair_dados(klines, [2, 3, 4])
            high, low, close = extr[2], extr[3], extr[4]

            if len(close) < 10:
                return np.array([]), np.array([])

            vol = self._calcular_volatilidade(close)
            ajuste = int(vol * 3)

            base = {"fastk": 5, "slowk": 3, "slowd": 3}
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

    def calcular_mfi(self, klines, periodo=14) -> np.ndarray:
        """
        Calcula o MFI (Money Flow Index).

        Args:
            klines: Lista de k-lines.
            periodo (int): Período para MFI.

        Returns:
            np.ndarray: Valores do MFI ou array vazio em caso de erro.
        """
        try:
            extr = self._extrair_dados(klines, [2, 3, 4, 5])
            high, low, close, volume = extr[2], extr[3], extr[4], extr[5]
            if len(close) < periodo:
                return np.array([])
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular MFI: {e}")
            return np.array([])

    def _calcular_volatilidade(self, close, periodo=14) -> float:
        """
        Calcula a volatilidade com base no desvio padrão.

        Args:
            close: Array de preços de fechamento.
            periodo (int): Período para cálculo.

        Returns:
            float: Valor da volatilidade ou 0.0 em caso de erro.
        """
        try:
            if len(close) < periodo:
                return 0.0
            stddev = talib.STDDEV(close, timeperiod=periodo)
            return (
                round(min(max(stddev[-1] / close[-1], 0.0), 1.0), 4)
                if stddev.size
                else 0.0
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular volatilidade: {e}")
            return 0.0

    def executar(self, dados_completos: dict, symbol: str, timeframe: str) -> bool:
        """
        Executa o cálculo dos indicadores osciladores e armazena resultados.

        Args:
            dados_completos: Dicionário com dados a serem processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em caso de erro, para não interromper o pipeline).
        """
        resultado_padrao = {
            "rsi": None,
            "estocastico": {"slowk": None, "slowd": None},
            "mfi": None,
            "volatilidade": 0.0,
        }

        try:
            if not self._validar_dados_completos(dados_completos, symbol, timeframe):
                dados_completos["osciladores"] = resultado_padrao
                return True

            crus = dados_completos.get("crus", [])
            rsi = self.calcular_rsi(crus, symbol, timeframe)
            slowk, slowd = self.calcular_estocastico(crus, timeframe)
            mfi = self.calcular_mfi(crus)
            close = self._extrair_dados(crus, [4])[4]
            volatilidade = self._calcular_volatilidade(close)

            resultado = {
                "rsi": float(rsi[-1]) if rsi.size else None,
                "estocastico": {
                    "slowk": float(slowk[-1]) if slowk.size else None,
                    "slowd": float(slowd[-1]) if slowd.size else None,
                },
                "mfi": float(mfi[-1]) if mfi.size else None,
                "volatilidade": volatilidade,
            }

            dados_completos["osciladores"] = resultado
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral ao executar: {e}")
            if isinstance(dados_completos, dict):
                dados_completos["osciladores"] = resultado_padrao
            return True
