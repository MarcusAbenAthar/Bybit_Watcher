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

import logging
import os
from typing import List, Dict, Optional
import ccxt
import requests
from plugins.plugin import Plugin
from utils.singleton import Singleton

logger = logging.getLogger(__name__)


class Conexao(Plugin, metaclass=Singleton):
    """Plugin para conexão com a Bybit."""

    # Identificador explícito do plugin
    PLUGIN_NAME = "conexao"
    PLUGIN_TYPE = "essencial"

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
        self.inicializado = False  # Atributo necessário para verificação

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
            self.inicializado = True  # Correção do bug de conexão
            logger.info("Plugin Conexao inicializado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar conexão: {e}")
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

    def validar_mercado(self, dados):
        """
        Valida se um mercado atende aos critérios rigorosos de análise.

        Regras de Ouro aplicadas:
        - Criterioso: Validação rigorosa dos dados
        - Seguro: Checagem de todos os parâmetros
        - Certeiro: Apenas mercados que atendam 100% dos critérios

        Args:
            dados (dict): Dados do mercado da Bybit

        Returns:
            bool: True se o mercado é válido para análise
        """
        try:
            # Validação criteriosa dos dados básicos
            if not all(k in dados for k in ["type", "quote", "active", "baseVolume"]):
                logger.warning("Dados incompletos do mercado")
                return False

            # Regras rigorosas de validação
            regras = {
                "tipo_mercado": dados["type"] == "swap",
                "moeda_quote": dados["quote"] == "USDT",
                "mercado_ativo": dados["active"] is True,
                "volume_minimo": float(dados["baseVolume"])
                > 1000000,  # Volume mínimo 1M USDT
            }

            # Checagem detalhada
            for regra, resultado in regras.items():
                if not resultado:
                    logger.debug(f"Mercado falhou na regra: {regra}")
                    return False

            logger.info(f"Mercado validado com sucesso: {dados['symbol']}")
            return True

        except Exception as erro:
            logger.error(f"Erro na validação do mercado: {str(erro)}")
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
