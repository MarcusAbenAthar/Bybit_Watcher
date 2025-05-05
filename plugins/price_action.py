"""
Plugin de análise de price action com reconhecimento de padrões simples de candle,
baseado em corpo, pavio e direção.
"""

from utils.logging_config import get_logger, log_rastreamento
import numpy as np
from plugins.plugin import Plugin
from utils.config import carregar_config
from utils.plugin_utils import validar_klines

logger = get_logger(__name__)


class PriceAction(Plugin):
    """
    Plugin de análise de Price Action (PA) para identificar padrões de reversão e continuidade.
    - Responsabilidade única: análise de price action.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "price_action"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "price_action", "pa"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin PriceAction.
        """
        return []

    PLUGIN_NAME = "price_action"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["price_action", "candles", "direcional", "analise"]
    PLUGIN_PRIORIDADE = 40

    def __init__(self, **kwargs):
        """
        Inicializa o plugin de price action.
        """
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("price_action", {}).copy()
            if "plugins" in config and "price_action" in config["plugins"]
            else {}
        )
        self._min_klines = 20  # Mínimo de k-lines para análise
        self._doji_threshold = 0.1  # Proporção corpo/range para doji

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações (ex.: número mínimo de k-lines).

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            self._min_klines = config.get("price_action", {}).get(
                "min_klines", self._min_klines
            )
            self._doji_threshold = config.get("price_action", {}).get(
                "doji_threshold", self._doji_threshold
            )

            if not (isinstance(self._min_klines, int) and self._min_klines > 0):
                logger.error(f"[{self.nome}] min_klines inválido: {self._min_klines}")
                return False
            if not (
                isinstance(self._doji_threshold, (int, float))
                and 0.0 < self._doji_threshold < 1.0
            ):
                logger.error(
                    f"[{self.nome}] doji_threshold inválido: {self._doji_threshold}"
                )
                return False

            logger.info(
                f"[{self.nome}] inicializado com min_klines={self._min_klines}, "
                f"doji_threshold={self._doji_threshold}"
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
            log_rastreamento(
                componente=f"price_action/{symbol}-{timeframe}",
                acao="validacao_falha",
                detalhes="klines não é lista",
            )
            return False
        if len(klines) < 20:
            logger.error(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines, "
                f"requer 20"
            )
            log_rastreamento(
                componente=f"price_action/{symbol}-{timeframe}",
                acao="validacao_falha",
                detalhes=f"klines insuficientes: {len(klines)}",
            )
            return False
        for kline in klines:
            if not isinstance(kline, (list, tuple)) or len(kline) < 6:
                logger.error(
                    f"[{self.nome}] K-line malformada para {symbol} - {timeframe}: {kline}"
                )
                log_rastreamento(
                    componente=f"price_action/{symbol}-{timeframe}",
                    acao="validacao_falha",
                    detalhes=f"kline malformada: {kline}",
                )
                return False
            try:
                for i in [1, 2, 3, 4, 5]:
                    float(kline[i])
            except (TypeError, ValueError):
                logger.error(
                    f"[{self.nome}] Valor não numérico em k-line para {symbol} - {timeframe}: {kline}"
                )
                log_rastreamento(
                    componente=f"price_action/{symbol}-{timeframe}",
                    acao="validacao_falha",
                    detalhes=f"valor não numérico em kline: {kline}",
                )
                return False
        return True

    def executar(self, *args, **kwargs) -> bool:
        from utils.logging_config import log_rastreamento

        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"price_action/{symbol}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        resultado_padrao = {"price_action": {}}
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
            if not self._validar_klines(candles, symbol, timeframe):
                return resultado_padrao
            resultado = self.gerar_sinal(candles)
            logger.debug(
                f"[{self.nome}] Price action para {symbol}-{timeframe}: {resultado}"
            )
            if isinstance(dados_completos, dict):
                dados_completos["price_action"] = resultado
            log_rastreamento(
                componente=f"price_action/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"price_action={resultado}",
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return resultado_padrao

    def gerar_sinal(self, klines: list) -> dict:
        """
        Gera sinal baseado em padrões de price action.

        Args:
            klines: Lista de k-lines.

        Returns:
            dict: Sinal com direção, força, confiança e padrão.
        """
        try:
            dados = self._extrair_dados(klines, [1, 2, 3, 4, 5])
            open_, high, low, close, volume = (
                dados[1],
                dados[2],
                dados[3],
                dados[4],
                dados[5],
            )
            from utils.logging_config import log_rastreamento

            log_rastreamento(
                componente=f"price_action/gerar_sinal",
                acao="dados_extraidos",
                detalhes=f"len_close={len(close)}, close_exemplo={close[-5:].tolist() if len(close) >= 5 else close.tolist()}",
            )

            ultimo = {
                "open": open_[-1],
                "high": high[-1],
                "low": low[-1],
                "close": close[-1],
                "volume": volume[-1],
            }

            padrao = self._identificar_padrao(ultimo)
            direcao = self._analisar_direcao(ultimo)
            forca = self._calcular_forca(ultimo, klines)

            vol_rel = (
                volume[-1] / np.mean(volume[-10:]) if np.mean(volume[-10:]) > 0 else 1.0
            )
            confianca = round(min(max(forca * (0.7 + 0.3 * vol_rel), 0.0), 1.0), 2)
            direcao_final = direcao if padrao != "doji" else "LATERAL"
            forca_label = (
                "FORTE"
                if confianca >= 0.7
                else "MÉDIA" if confianca >= 0.3 else "FRACA"
            )

            resultado = {
                "direcao": direcao_final,
                "forca": forca_label,
                "confianca": confianca,
                "padrao": padrao,
            }
            log_rastreamento(
                componente=f"price_action/gerar_sinal",
                acao="sinal_calculado",
                detalhes=f"resultado={resultado}",
            )
            return resultado
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao gerar sinal: {e}", exc_info=True)
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "padrao": None,
            }

    def _identificar_padrao(self, candle: dict) -> str:
        """
        Identifica o padrão do candle (ex.: alta, baixa, doji).

        Args:
            candle: Dicionário com open, high, low, close.

        Returns:
            str: Padrão identificado.
        """
        try:
            corpo = abs(candle["close"] - candle["open"])
            range_ = candle["high"] - candle["low"]
            if range_ == 0:
                return "indefinido"
            proporcao = corpo / range_
            if proporcao < self._doji_threshold:
                return "doji"
            return "alta" if candle["close"] > candle["open"] else "baixa"
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao identificar padrão: {e}")
            return "indefinido"

    def _calcular_forca(self, candle: dict, klines: list) -> float:
        """
        Calcula a força do padrão com base no corpo e volume.

        Args:
            candle: Dicionário com open, high, low, close, volume.
            klines: Lista de k-lines para contexto.

        Returns:
            float: Força do padrão (0.0 a 1.0).
        """
        try:
            corpo = abs(candle["close"] - candle["open"])
            range_ = candle["high"] - candle["low"]
            forca_base = corpo / range_ if range_ > 0 else 0.0

            # Incorporar volume
            dados = self._extrair_dados(klines, [5])
            volume = dados[5]
            vol_rel = (
                volume[-1] / np.mean(volume[-10:]) if np.mean(volume[-10:]) > 0 else 1.0
            )
            return round(min(max(forca_base * (0.7 + 0.3 * vol_rel), 0.0), 1.0), 4)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular força: {e}")
            return 0.0

    def _analisar_direcao(self, candle: dict) -> str:
        """
        Analisa a direção do candle.

        Args:
            candle: Dicionário com open, high, low, close.

        Returns:
            str: Direção (ALTA, BAIXA, LATERAL).
        """
        try:
            if candle["close"] > candle["open"]:
                return "ALTA"
            elif candle["close"] < candle["open"]:
                return "BAIXA"
            return "LATERAL"
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao analisar direção: {e}")
            return "LATERAL"

    def _extrair_dados(self, dados: list, indices: list) -> dict:
        """
        Extrai dados especificados das k-lines.

        Args:
            dados: Lista de k-lines.
            indices: Lista de índices a extrair (ex.: [1, 2, 3, 4]).

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

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "price_action": {
                "descricao": "Armazena sinais de price action, padrões identificados, faixas de entrada, score, contexto de mercado, observações e candle bruto para rastreabilidade e auditoria.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "padrao": "VARCHAR(50)",
                    "direcao": "VARCHAR(10)",
                    "forca": "DECIMAL(5,2)",
                    "confianca": "DECIMAL(5,2)",
                    "preco_entrada": "DECIMAL(18,8)",
                    "faixa_entrada_min": "DECIMAL(18,8)",
                    "faixa_entrada_max": "DECIMAL(18,8)",
                    "stop_loss": "DECIMAL(18,8)",
                    "take_profit": "DECIMAL(18,8)",
                    "volume": "DECIMAL(18,8)",
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
