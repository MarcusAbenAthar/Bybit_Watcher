"""
Gerenciador principal do bot.
Responsável por coordenar todas as operações do bot.
"""

import logging
import time
import ccxt
from plugins.plugin import Plugin
from plugins.validador_dados import ValidadorDados

logger = logging.getLogger(__name__)


class GerenciadorBot(Plugin):
    """Gerenciador principal do bot."""

    def __init__(self, config=None):
        super().__init__()
        self.nome = "Gerenciador Bot"
        self.descricao = "Gerencia operações principais do bot"
        self.config = config
        self.validador = ValidadorDados()
        self.pares_processados = set()
        self.timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

    def validar_mercado(self, dados):
        """
        Valida se o mercado está apto para análise.

        Args:
            dados (dict): Dados do mercado da Bybit

        Returns:
            bool: True se mercado válido para análise
        """
        try:
            symbol = dados.get("symbol", "Unknown")
            type_mercado = dados.get("type", "Unknown")
            volume = float(dados.get("baseVolume", 0))
            is_active = dados.get("active", False)

            # Filtrar apenas mercados swap
            if type_mercado != "swap":
                logger.debug(f"Mercado ignorado (não é swap): {symbol}")
                return False

            # Normalizar o símbolo (remover /USDT:USDT)
            symbol_normalizado = symbol.replace("/USDT:USDT", "")

            logger.info(
                f"Analisando mercado:"
                f"\n\tSymbol: {symbol_normalizado}"
                f"\n\tTipo: {type_mercado}"
                f"\n\tVolume: {volume}"
                f"\n\tAtivo: {is_active}"
            )

            # Outras validações...
            if not is_active:
                logger.debug(f"{symbol_normalizado}: Mercado inativo")
                return False

            if volume < 1000:  # Volume mínimo de 1000 USDT
                logger.debug(f"{symbol_normalizado}: Volume insuficiente ({volume})")
                return False

            logger.info(f"Mercado válido: {symbol_normalizado}")
            return True

        except Exception as e:
            logger.error(
                f"Erro ao validar mercado {dados.get('symbol', 'Unknown')}: {e}"
            )
            return False

    def processar_par(self, symbol, timeframe, exchange):
        """
        Processa um par específico.

        Args:
            symbol (str): Símbolo do par
            timeframe (str): Timeframe para análise
            exchange (Exchange): Instância da exchange

        Returns:
            list: Dados validados ou None se inválidos
        """
        try:
            # Verifica se já foi processado recentemente
            par_key = f"{symbol}-{timeframe}"
            if par_key in self.pares_processados:
                logger.debug(f"Par {par_key} já processado recentemente")
                return None

            logger.info(f"Coletando dados de {symbol} em {timeframe}")

            # Coleta dados com retry em caso de rate limit
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    dados = exchange.fetch_ohlcv(
                        symbol, timeframe, params={"category": "linear", "limit": 200}
                    )
                    break
                except ccxt.RateLimitExceeded:
                    retry_count += 1
                    wait_time = 5 * retry_count
                    logger.warning(
                        f"Rate limit atingido para {symbol}, tentativa {retry_count}. Aguardando {wait_time}s"
                    )
                    time.sleep(wait_time)
                    continue
                except Exception as e:
                    logger.error(f"Erro ao coletar dados de {symbol}: {e}")
                    return None

            if not dados or len(dados) < 200:
                logger.warning(f"Dados insuficientes para {symbol}-{timeframe}")
                return None

            # Adiciona ao set de processados
            self.pares_processados.add(par_key)

            logger.info(f"Dados coletados com sucesso para {symbol}-{timeframe}")
            return dados

        except Exception as e:
            logger.error(f"Erro ao processar {symbol}-{timeframe}: {e}")
            return None

    def processar_plugins(self, plugins, dados, symbol, timeframe):
        """
        Processa dados através dos plugins na ordem correta.

        Args:
            plugins (list): Lista de plugins
            dados (list): Dados OHLCV
            symbol (str): Símbolo do par
            timeframe (str): Timeframe
        """
        try:
            resultados = {}

            # 1. Processa indicadores
            for plugin in plugins:
                if plugin.nome in ["Indicadores de Tendência", "Médias Móveis"]:
                    resultado = plugin.executar(dados, symbol, timeframe)
                    if resultado:
                        chave = plugin.nome.lower().replace(" ", "_").replace("ê", "e")
                        resultados[chave] = resultado

            # 2. Processa sinais
            for plugin in plugins:
                if plugin.nome == "Sinais" and resultados:
                    plugin.executar(resultados, symbol, timeframe)

            # 3. Processa outros plugins
            for plugin in plugins:
                if plugin.nome not in [
                    "Indicadores de Tendência",
                    "Médias Móveis",
                    "Sinais",
                ]:
                    plugin.executar(dados, symbol, timeframe)

        except Exception as e:
            logger.error(f"Erro ao processar plugins: {e}")
