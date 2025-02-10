# plugins/conexao.py

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
# plugins/conexao.py

import os
import time
from typing import List, Dict, Optional, Tuple
import ccxt
import requests
from plugins.plugin import Plugin
from utils.singleton import singleton
from utils.logging_config import get_logger


logger = get_logger(__name__)


class Conexao(Plugin):
    """Plugin para conexão com a Bybit."""

    # Identificador explícito do plugin
    PLUGIN_NAME = "conexao"
    PLUGIN_TYPE = "essencial"

    # Singleton instance
    _instance = None

    def __new__(cls):
        """Implementa o padrão Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.inicializado = False
        return cls._instance

    def __init__(self):
        """Inicializa o plugin de conexão."""
        super().__init__()
        self.descricao = "Plugin de conexão com a Bybit"
        self.exchange = None
        self._mercado = "swap"
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
            logger.info("Iniciando conexão com Bybit...")
            super().inicializar(config)

            # Configura mercado
            self._mercado = os.getenv("BYBIT_MARKET", "swap")

            # Conecta com a exchange
            if not self.conectar_bybit():
                return False

            # Carrega mercados disponíveis
            self._pares_usdt = self.filtrar_pares_usdt()

            self.inicializado = True
            logger.info("Conexão Bybit inicializada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar conexão: {e}")
            return False

    def _sincronizar_timestamp(self) -> Tuple[bool, int]:
        """
        Sincroniza timestamp com o servidor da Bybit.

        Returns:
            Tuple[bool, int]: (sucesso, diferença de tempo em ms)
        """
        try:
            # Obtém timestamp do servidor
            response = requests.get("https://api.bybit.com/v5/market/time")
            if response.status_code != 200:
                return False, 0

            server_time = response.json()["time"]
            local_time = int(time.time() * 1000)
            time_offset = int(server_time) - local_time

            logger.info(f"Diferença de tempo: {time_offset}ms")
            return True, time_offset

        except Exception as e:
            logger.error(f"Erro ao sincronizar timestamp: {e}")
            return False, 0

    def _conectar_com_retry(self, max_tentativas: int = 3) -> Optional[ccxt.Exchange]:
        """
        Tenta conectar à Bybit com retry e backoff exponencial.

        Args:
            max_tentativas: Número máximo de tentativas

        Returns:
            Optional[ccxt.Exchange]: Instância da exchange ou None se falhar
        """
        tentativa = 0
        while tentativa < max_tentativas:
            try:
                # Obtém credenciais
                api_key = os.getenv("BYBIT_API_KEY")
                api_secret = os.getenv("BYBIT_API_SECRET")

                if not api_key or not api_secret:
                    raise ValueError("Credenciais Bybit não encontradas no .env")

                # Sincroniza timestamp primeiro
                sincronizado, time_offset = self._sincronizar_timestamp()
                if not sincronizado:
                    raise Exception("Falha ao sincronizar timestamp")

                # Configura cliente com diferença de tempo
                exchange = ccxt.bybit(
                    {
                        "apiKey": api_key,
                        "secret": api_secret,
                        "enableRateLimit": True,
                        "options": {
                            "defaultType": self._mercado,
                            "recvWindow": 60000,  # 60 segundos
                            "adjustForTimeDifference": True,
                            "timeDifference": time_offset,
                        },
                    }
                )

                # Testa conexão
                exchange.load_markets()
                logger.info("Conexão estabelecida com Bybit (Produção)")
                return exchange

            except Exception as e:
                tentativa += 1
                if tentativa < max_tentativas:
                    wait_time = 2**tentativa  # Backoff exponencial
                    logger.warning(
                        f"Tentativa {tentativa} falhou: {e}. Aguardando {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Todas as tentativas falharam: {e}")
                    return None

        return None

    def conectar_bybit(self) -> bool:
        """
        Estabelece conexão com a Bybit.

        Returns:
            bool: True se conectado com sucesso
        """
        try:
            # Tenta conectar com retry
            exchange = self._conectar_com_retry()
            if not exchange:
                return False

            self.exchange = exchange
            return True

        except Exception as e:
            logger.error(f"Erro ao conectar na Bybit: {e}")
            return False

    def filtrar_pares_usdt(self) -> List[str]:
        """
        Filtra pares USDT válidos.

        Returns:
            List[str]: Lista de pares válidos
        """
        try:
            if not self.exchange:
                return []

            pares = []
            mercados = self.exchange.load_markets()

            for simbolo, dados in mercados.items():
                if self.validar_mercado(dados):
                    pares.append(simbolo)

            logger.info(f"Pares USDT encontrados: {len(pares)}")
            return pares

        except Exception as e:
            logger.error(f"Erro ao filtrar pares: {e}")
            return []

    def validar_mercado(self, dados: Dict) -> bool:
        """
        Valida se mercado atende critérios.

        Args:
            dados: Dados do mercado

        Returns:
            bool: True se mercado válido
        """
        try:
            volume_min = float(os.getenv("VOLUME_MIN", "1000000"))
            return (
                dados.get("type") == "swap"
                and dados.get("quote") == "USDT"
                and dados.get("active") is True
                and float(dados.get("baseVolume", 0)) > volume_min
            )
        except Exception as e:
            logger.error(f"Erro na validação: {e}")
            return False

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

    def obter_pares(self) -> List[str]:
        """
        Retorna lista de pares USDT disponíveis.

        Returns:
            List[str]: Lista de pares USDT
        """
        try:
            if not self._pares_usdt:
                self._pares_usdt = self.filtrar_pares_usdt()
            return self._pares_usdt

        except Exception as e:
            logger.error(f"Erro ao obter pares: {e}")
            return []

    def obter_klines(self, symbol: str, timeframe: str) -> List[Tuple]:
        """
        Obtém dados OHLCV do par.

        Args:
            symbol: Par de trading
            timeframe: Intervalo de tempo

        Returns:
            List[Tuple]: Lista de candles OHLCV
        """
        try:
            if not self.exchange:
                return []

            # Obtém últimos 100 candles usando API v5
            params = {
                "category": "linear",
                "symbol": symbol,
                "interval": timeframe,
                "limit": 100,
            }
            response = requests.get(
                "https://api.bybit.com/v5/market/kline", params=params
            )

            if response.status_code != 200:
                logger.error(f"Erro ao obter klines: Status {response.status_code}")
                return []

            data = response.json()
            if data["retCode"] != 0:
                logger.error(f"Erro ao obter klines: {data['retMsg']}")
                return []

            # Formata dados
            dados = []
            for k in data["result"]["list"]:
                dados.append(
                    (
                        symbol,
                        timeframe,
                        int(k[0]),  # timestamp
                        float(k[1]),  # open
                        float(k[2]),  # high
                        float(k[3]),  # low
                        float(k[4]),  # close
                        float(k[5]),  # volume
                    )
                )

            return dados

        except Exception as e:
            logger.error(f"Erro ao obter klines de {symbol} {timeframe}: {e}")
            return []

    def finalizar(self):
        """Finaliza a conexão com a exchange."""
        try:
            if self.exchange:
                self.exchange = None

            self.inicializado = False
            logger.info("Conexão Bybit finalizada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao finalizar conexão: {e}")
