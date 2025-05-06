"""
Plugin de cálculo de alavancagem.
Responsabilidade única: cálculo de alavancagem para operações.
Não deve registrar, inicializar ou finalizar automaticamente.
Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
"""

import numpy as np
import talib

from plugins.plugin import Plugin
from utils.logging_config import get_logger
from utils.config import carregar_config
from utils.plugin_utils import validar_klines

logger = get_logger(__name__)


class CalculoAlavancagem(Plugin):
    """
    Plugin para cálculo de alavancagem segura e eficiente.
    - Responsabilidade única: cálculo de alavancagem.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "calculo_alavancagem"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["alavancagem", "gerenciamento", "risco"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin CalculoAlavancagem.
        """
        return []

    PLUGIN_NAME = "calculo_alavancagem"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "volatilidade", "alavancagem"]
    PLUGIN_PRIORIDADE = 85

    def __init__(self, **kwargs):
        """
        Plugin para cálculo dinâmico de alavancagem baseado em volatilidade e confiança.
        """
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("calculo_alavancagem", {}).copy()
            if "plugins" in config and "calculo_alavancagem" in config["plugins"]
            else {}
        )
        self._alav_max = 5.0  # Valor padrão de segurança
        self._alav_min = 1.0
        self._confianca_fallback = 0.3  # Fallback para confiança inválida

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com a configuração do sistema.

        Args:
            config: Configuração geral do sistema.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                return False

            self._config = config
            trading_cfg = config.get("trading", {})
            self._alav_max = trading_cfg.get("alavancagem_maxima", self._alav_max)
            self._alav_min = trading_cfg.get("alavancagem_minima", self._alav_min)
            self._confianca_fallback = trading_cfg.get(
                "confianca_fallback", self._confianca_fallback
            )

            logger.info(
                f"[{self.nome}] inicializado com alavancagem [{self._alav_min}x - {self._alav_max}x], "
                f"confianca_fallback={self._confianca_fallback}"
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

        if len(klines) < 14:
            logger.error(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines"
            )
            return False

        for kline in klines:
            if not isinstance(kline, (list, tuple)) or len(kline) < 6:
                logger.error(
                    f"[{self.nome}] K-line malformada para {symbol} - {timeframe}: {kline}"
                )
                return False
            try:
                # Verificar se high, low, close são numéricos
                for i in [2, 3, 4]:  # Índices 2, 3, 4
                    float(kline[i])
            except (TypeError, ValueError):
                logger.error(
                    f"[{self.nome}] Valor não numérico em k-line para {symbol} - {timeframe}: {kline}"
                )
                return False

        return True

    def executar(self, *args, **kwargs):
        resultado_padrao = {"alavancagem": self._alav_min}
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                return resultado_padrao
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                return resultado_padrao
            crus = dados_completos.get("crus", [])
            if not self._validar_klines(crus, symbol, timeframe):
                return resultado_padrao
            direcao = kwargs.get("direcao", None)
            confianca = kwargs.get("confianca", 0.0)
            alavancagem = self.calcular_alavancagem(
                crus, direcao=direcao, confianca=confianca
            )
            logger.debug(
                f"[{self.nome}] Alavancagem atribuída para {symbol}-{timeframe}: {alavancagem}x"
            )
            return {"alavancagem": alavancagem}
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return resultado_padrao

    def calcular_alavancagem(
        self, crus: list, direcao: str = None, confianca: float = 0.0
    ) -> float:
        """
        Calcula a alavancagem com base no ATR (volatilidade) e na confiança do sinal.
        Retorna uma alavancagem ajustada, limitada pelos valores definidos na configuração.

        Args:
            crus: Lista de k-lines.
            direcao: Direção do sinal (ex.: ALTA, BAIXA, NEUTRO).
            confianca: Confiança do sinal (0.0 a 1.0).

        Returns:
            float: Alavancagem calculada.
        """
        try:
            highs = np.array([float(c[2]) for c in crus], dtype=np.float64)
            lows = np.array([float(c[3]) for c in crus], dtype=np.float64)
            closes = np.array([float(c[4]) for c in crus], dtype=np.float64)

            atr = talib.ATR(highs, lows, closes, timeperiod=14)
            if atr is None or atr.size == 0 or closes[-1] == 0:
                logger.warning(f"[{self.nome}] ATR inválido ou preço atual zerado")
                return self._alav_min

            atr_atual = atr[-1]
            preco_atual = closes[-1]
            volatilidade = atr_atual / preco_atual

            if direcao and direcao.upper() == "NEUTRO":
                logger.info(
                    f"[{self.nome}] Direção NEUTRO detectada — alavancagem mínima forçada"
                )
                return self._alav_min

            # Alavancagem base ajustada pela volatilidade
            if volatilidade < 0.001:
                alav_base = self._alav_max
            elif volatilidade < 0.005:
                alav_base = (self._alav_max + self._alav_min) / 2
            else:
                alav_base = self._alav_min

            try:
                confianca = float(confianca)
                if not 0.0 <= confianca <= 1.0:
                    logger.warning(
                        f"[{self.nome}] Confiança fora do intervalo [0.0, 1.0]: {confianca}, usando fallback"
                    )
                    confianca = self._confianca_fallback
            except (ValueError, TypeError):
                logger.warning(
                    f"[{self.nome}] Confiança inválida: {confianca}, usando fallback {self._confianca_fallback}"
                )
                confianca = self._confianca_fallback

            fator_conf = confianca if confianca > 0 else self._confianca_fallback
            alav_final = alav_base * fator_conf

            resultado = round(max(self._alav_min, min(alav_final, self._alav_max)), 2)

            logger.debug(
                f"[{self.nome}] Alavancagem final: {resultado}x | Vol: {volatilidade:.5f} | Conf: {confianca:.2f}"
            )
            return resultado

        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro no cálculo de alavancagem: {e}", exc_info=True
            )
            return self._alav_min

    @property
    def plugin_tabelas(self) -> dict:
        """
        Define as tabelas do plugin conforme padrão institucional (regras de ouro).
        """
        return {
            "alavancagem_calculada": {
                "descricao": "Armazena os cálculos de alavancagem sugeridos pelo plugin, incluindo faixas, score e contexto.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "alavancagem": "DECIMAL(5,2)",
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
