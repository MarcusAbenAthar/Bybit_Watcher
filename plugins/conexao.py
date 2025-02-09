"""
Plugin para conexão com a Bybit.

Regras de Ouro:
1. Autonomo - Gerencia conexão automaticamente
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros
4. Certeiro - Operações precisas
5. Eficiente - Performance otimizada
6. Clareza - Bem documentado
7. Modular - Responsabilidade única
8. Plugins - Interface padronizada
9. Testável - Métodos isolados
10. Documentado - Docstrings completos
"""

import os
from typing import List, Dict, Optional
import ccxt
from plugins.plugin import Plugin
from utils.singleton import singleton
from utils.logging_config import get_logger

logger = get_logger(__name__)


@singleton
class Conexao(Plugin):
    """Plugin para conexão com a Bybit."""

    def __init__(self):
        """Inicializa o plugin de conexão."""
        super().__init__()
        # Atributos obrigatórios da classe base
        self.nome = "conexao"  # Nome deve corresponder ao arquivo
        self.descricao = "Plugin de conexão com a Bybit"

        # Atributos específicos deste plugin
        self.exchange = None
        self._mercado = os.getenv("BYBIT_MARKET", "swap")
        self._pares_usdt = []

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com a Bybit.

        Args:
            config: Configurações do plugin

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            # Inicializa classe base
            if not super().inicializar(config):
                return False

            # Conecta com a exchange
            if not self._conectar_bybit():
                return False

            logger.info("Plugin Conexao inicializado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar Conexao: {e}")
            return False

    def _conectar_bybit(self) -> bool:
        """
        Estabelece conexão com a Bybit.

        Returns:
            bool: True se conectado com sucesso
        """
        try:
            # Obtém credenciais
            api_key = os.getenv("BYBIT_API_KEY")
            api_secret = os.getenv("BYBIT_API_SECRET")

            if not api_key or not api_secret:
                raise ValueError("Credenciais da API não encontradas")

            # Configura cliente
            self.exchange = ccxt.bybit(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "options": {"defaultType": self._mercado},
                }
            )

            # Carrega mercados
            self.exchange.load_markets()

            # Atualiza pares USDT
            self._pares_usdt = [
                symbol for symbol in self.exchange.symbols if symbol.endswith("/USDT")
            ]

            logger.info("Conexão estabelecida com Bybit")
            return True

        except Exception as e:
            logger.error(f"Erro ao conectar com Bybit: {e}")
            return False

    def obter_pares_usdt(self) -> List[str]:
        """
        Obtém lista de pares USDT disponíveis.

        Returns:
            List[str]: Lista de pares USDT
        """
        return self._pares_usdt

    def executar(self) -> bool:
        """
        Executa ciclo do plugin.

        Returns:
            bool: True se executado com sucesso
        """
        try:
            if not self.exchange:
                return False

            # Verifica conexão
            self.exchange.fetch_balance()
            return True

        except Exception as e:
            logger.error(f"Erro no ciclo de execução: {e}")
            return False

    def finalizar(self):
        """Finaliza a conexão com a exchange."""
        try:
            if self.exchange:
                self.exchange = None

            self.inicializado = False
            logger.info("Conexão finalizada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao finalizar conexão: {e}")
