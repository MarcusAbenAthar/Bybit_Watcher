"""Plugin para gerenciar autenticação e conexão com a API da Bybit."""

import ccxt
from plugins.plugin import Plugin
from utils.config import carregar_config
from utils.logging_config import get_logger
import json

logger = get_logger(__name__)


class Conexao(Plugin):
    """Plugin responsável por autenticar e fornecer instância de cliente Bybit."""

    PLUGIN_NAME = "conexao"
    PLUGIN_CATEGORIA = "infraestrutura"
    PLUGIN_TAGS = ["conexao", "bybit", "api"]
    PLUGIN_PRIORIDADE = 5

    def __init__(self, gerente=None):
        super().__init__()
        self.exchange = None
        self._gerente = gerente
        self._config = None
        self.pares_info = None

    def inicializar(self, config=None) -> bool:
        """Inicializa a conexão com a Bybit."""
        try:
            self._config = carregar_config()
            bybit_cfg = self._config.get("bybit", {})
            api_key = bybit_cfg.get("api_key")
            api_secret = bybit_cfg.get("api_secret")
            base_url = bybit_cfg.get("base_url")
            market = bybit_cfg.get("market", "linear")  # Padrão de config.py
            testnet = bybit_cfg.get("testnet", True)

            if not all([api_key, api_secret, base_url]):
                logger.error("Configuração da Bybit incompleta.")
                return False

            # Se quiser forçar swap no bot independentemente da config:
            market = "swap"

            self.exchange = ccxt.bybit({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": market},
            })

            # Ajusta URL se estiver em ambiente de teste
            if testnet:
                self.exchange.urls['api'] = {
                    'public': base_url,
                    'private': base_url,
                }

            logger.info("Conexão com Bybit inicializada com sucesso.")
            logger.debug(f"Conectado ao mercado: {market.upper()}")
            return True
        except Exception as e:
            logger.error(
                f"Erro ao inicializar conexão com Bybit: {e}", exc_info=True)
            return False

    def obter_cliente(self):
        """Retorna a instância autenticada do cliente Bybit."""
        if not self.exchange:
            logger.warning(
                "Cliente Bybit não inicializado. Chame inicializar() antes.")
        return self.exchange

    def listar_pares(self) -> list:
        """Retorna a lista de IDs dos símbolos disponíveis na Bybit."""
        if not self.exchange:
            logger.error(
                "Cliente Bybit não inicializado, impossível listar pares.")
            return []
        try:
            markets = self.exchange.fetch_markets()
            with open("pares.json", "w") as f:
                json.dump(markets, f, indent=4)

            # Aqui, corrigido para usar o ID dos mercados (não o symbol formatado)
            self.pares_info = {m["id"]: m for m in markets}
            return list(self.pares_info.keys())
        except Exception as e:
            logger.error(
                f"[conexao] Erro ao buscar mercados: {e}", exc_info=True)
            return []

    def obter_info_par(self, symbol: str) -> dict:
        """Retorna informações detalhadas de um par de negociação."""
        if not self.pares_info:
            logger.warning("Informações de pares ainda não carregadas.")
            return {}
        return self.pares_info.get(symbol, {})

    def finalizar(self):
        """Finaliza a conexão com a Bybit."""
        try:
            self.exchange = None
            super().finalizar()
            logger.info("Conexão com Bybit finalizada.")
        except Exception as e:
            logger.error(
                f"Erro ao finalizar conexão Bybit: {e}", exc_info=True)
