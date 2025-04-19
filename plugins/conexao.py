"""Plugin para conexão com a API da Bybit."""

import ccxt
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Conexao(Plugin):
    """Classe para gerenciar a conexão com a Bybit."""

    PLUGIN_NAME = "conexao"
    PLUGIN_CATEGORIA = "infraestrutura"
    PLUGIN_TAGS = ["conexao", "bybit", "api"]
    PLUGIN_PRIORIDADE = 10

    def __init__(self, gerente=None):
        """Inicializa o plugin de conexão."""
        super().__init__()
        self.exchange = None
        self._pares_usdt = []
        self._gerente = gerente
        self._mercado = None
        self._limits = {
            "1m": 200,
            "5m": 200,
            "15m": 200,
            "1h": 100,
            "4h": 100,
        }  # Pode ser sobrescrito por config
        logger.debug("Instância de Conexao criada.")

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com a Bybit usando config.

        Args:
            config: Dicionário de configuração geral do sistema.

        Returns:
            bool: True se sucesso, False caso contrário.
        """
        try:
            logger.debug("Inicializando plugin de conexão...")
            if not super().inicializar(config):
                logger.error("Inicialização base falhou.")
                return False

            bybit_cfg = config.get("bybit", {})
            self._mercado = bybit_cfg.get("market", "linear")
            api_key = bybit_cfg.get("api_key")
            api_secret = bybit_cfg.get("api_secret")
            base_url = bybit_cfg.get("base_url")

            if not all([api_key, api_secret, base_url]):
                logger.error("Configuração da Bybit incompleta.")
                return False

            self.exchange = ccxt.bybit(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "options": {"defaultType": self._mercado},
                    "urls": {
                        "api": {
                            "public": base_url,
                            "private": base_url,
                            "v5public": base_url,
                            "v5private": base_url,
                        }
                    },
                }
            )

            self.exchange.load_markets()
            self._pares_usdt = [
                s for s in self.exchange.symbols if s.endswith("/USDT:USDT")
            ]

            # Atualiza limits se vierem de config
            if "limits" in config and isinstance(config["limits"], dict):
                self._limits.update(config["limits"])
                logger.debug(f"Limits configurados: {self._limits}")

            logger.info(
                f"Conexão com Bybit *** {'TESTNET' if bybit_cfg.get('testnet') else 'MAINNET'})***  inicializada com sucesso."
            )
            return True

        except Exception as e:
            logger.exception(f"Erro ao inicializar conexao: {e}")
            return False

    def _validar_klines(self, klines: list, symbol: str, timeframe: str) -> bool:
        """Valida o formato das k-lines retornadas."""
        if not isinstance(klines, list) or not klines:
            logger.warning(
                f"[{self.nome}] Klines vazios ou inválidos para {symbol} {timeframe}"
            )
            return False

        for kline in klines:
            if not isinstance(kline, list) or len(kline) != 6:
                logger.error(f"[{self.nome}] K-line malformada: {kline}")
                return False
            try:
                for i in range(1, 6):
                    float(kline[i])
            except (TypeError, ValueError):
                logger.error(f"[{self.nome}] Valor inválido em k-line: {kline}")
                return False

        return True

    def obter_klines(self, symbol: str, timeframe: str, limit: int = 100):
        """Obtém klines da Bybit."""
        try:
            if not self.exchange:
                logger.error("Exchange não inicializada")
                return None

            if symbol not in self._pares_usdt:
                logger.error(f"[{self.nome}] Símbolo inválido: {symbol}")
                return None

            klines = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.debug(f"[{self.nome}] Klines recebidos ({len(klines)})")

            return klines if self._validar_klines(klines, symbol, timeframe) else None

        except Exception as e:
            logger.exception(f"[{self.nome}] Erro ao obter klines: {e}")
            return None

    def executar(self, *args, **kwargs) -> bool:
        """Executa a obtenção de klines e armazena em dados_completos."""
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes.")
                return True

            if not isinstance(dados_completos, dict):
                logger.warning(f"[{self.nome}] dados_completos deve ser dict.")
                return True

            limit = self._limits.get(timeframe, 50)
            klines = self.obter_klines(symbol, timeframe, limit)

            if klines:
                dados_completos["crus"] = klines
                logger.debug(f"[{self.nome}] Klines adicionados.")
            else:
                logger.warning(f"[{self.nome}] Nenhum kline recebido.")

            return True

        except Exception as e:
            logger.exception(f"[{self.nome}] Erro ao executar conexao: {e}")
            return True

    def obter_pares_usdt(self):
        """Retorna os pares USDT disponíveis."""
        return self._pares_usdt

    def finalizar(self):
        """Finaliza a conexão com a Bybit."""
        try:
            if self.exchange:
                self.exchange.close()
                logger.info(f"[{self.nome}] Conexão finalizada")
        except Exception as e:
            logger.exception(f"[{self.nome}] Erro ao finalizar conexao: {e}")
