"""Plugin para gerenciar autenticação e conexão com a API da Bybit."""

import ccxt
from plugins.plugin import Plugin
from utils.config import carregar_config
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Conexao(Plugin):
    """
    Plugin responsável por autenticar e fornecer instância de cliente Bybit.

    - Busca sempre as configurações do arquivo config.py.
    - Não executa operações de mercado diretamente.
    - Fornece métodos para obter cliente autenticado.
    """

    PLUGIN_NAME = "conexao"
    PLUGIN_CATEGORIA = "infraestrutura"
    PLUGIN_TAGS = ["conexao", "bybit", "api"]
    PLUGIN_PRIORIDADE = 5  # Prioridade máxima para garantir inicialização antecipada

    def __init__(self, gerente=None):
        super().__init__()
        self.exchange = None
        self._gerente = gerente
        self._config = None

    def inicializar(self, config=None) -> bool:
        """
        Inicializa a conexão com a Bybit usando sempre as configurações do config.py.
        Compatível com o pipeline do gerenciador de plugins (aceita config, mas ignora).

        Args:
            config (dict, opcional): Não utilizado, apenas para compatibilidade.

        Returns:
            bool: True se sucesso, False caso contrário.
        """
        """
        Inicializa a conexão com a Bybit usando sempre as configurações do config.py.

        Returns:
            bool: True se sucesso, False caso contrário.
        """
        try:
            self._config = carregar_config()
            bybit_cfg = self._config.get("bybit", {})
            api_key = bybit_cfg.get("api_key")
            api_secret = bybit_cfg.get("api_secret")
            base_url = bybit_cfg.get("base_url")
            market = bybit_cfg.get("market", "linear")
            testnet = bybit_cfg.get("testnet", True)

            if not all([api_key, api_secret, base_url]):
                logger.error("Configuração da Bybit incompleta.")
                return False

            self.exchange = ccxt.bybit({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "urls": {"api": base_url},
                "options": {"defaultType": market},
                "test": testnet,
            })
            logger.info("Conexão com Bybit inicializada com sucesso.")
            return True
        except Exception as e:
            logger.error(
                f"Erro ao inicializar conexão com Bybit: {e}", exc_info=True)
            return False

    def obter_cliente(self):
        """
        Retorna a instância autenticada do cliente Bybit.
        """
        if not self.exchange:
            logger.warning(
                "Cliente Bybit não inicializado. Chame inicializar() antes.")
        return self.exchange

    def finalizar(self):
        """
        Finaliza a conexão (limpa o cliente e garante shutdown seguro).
        """
        try:
            self.exchange = None
            super().finalizar()
            logger.info("Conexão com Bybit finalizada.")
        except Exception as e:
            logger.error(f"Erro ao finalizar conexão Bybit: {e}")
