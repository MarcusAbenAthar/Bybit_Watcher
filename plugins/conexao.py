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


logger = logging.getLogger(__name__)


class Conexao(Plugin):
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
        # Corrige para futuros perpétuos
        self._mercado = os.getenv("BYBIT_MARKET", "linear")
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
            logger.info("Conexão estabelecida com sucesso")
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

            # Atualiza pares USDT (apenas futuros perpétuos)
            self._pares_usdt = [
                symbol
                for symbol in self.exchange.symbols
                if symbol.endswith("/USDT:USDT")
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

    def obter_pares(self) -> List[str]:
        """
        Alias para obter_pares_usdt para compatibilidade.

        Returns:
            List[str]: Lista de pares USDT
        """
        return self.obter_pares_usdt()

    def obter_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> Optional[List]:
        """
        Obtém dados OHLCV para um par e timeframe.

        Args:
            symbol: Par de trading
            timeframe: Intervalo de tempo
            limit: Número de candles a serem obtidos (padrão: 100)

        Returns:
            Optional[List]: Lista de candles OHLCV ou None se falhar
        """
        try:
            if not self.exchange:
                logger.error("Exchange não inicializada")
                return None

            # Obtém os últimos 'limit' candles
            klines = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not klines:
                logger.warning(f"Nenhum dado OHLCV para {symbol} {timeframe}")
                return None

            return klines

        except Exception as e:
            logger.error(f"Erro ao obter klines para {symbol} {timeframe}: {e}")
            return None

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

    def executar(self, *args, **kwargs) -> bool:
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol", "BTCUSDT")
            timeframe = kwargs.get("timeframe", "1h")
            limit = kwargs.get("limit", 100)

            if not dados_completos:
                logger.error("Estrutura de dados completa não fornecida")
                return False

            klines = self.obter_klines(symbol, timeframe, limit)
            if not klines:
                logger.warning(f"Falha ao obter klines para {symbol} ({timeframe})")
                return False

            dados_completos["crus"] = klines
            return True
        except Exception as e:
            logger.error(f"Erro ao executar Conexao: {e}")
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
