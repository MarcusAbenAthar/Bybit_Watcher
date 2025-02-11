"""
Gerenciador principal do bot.

Regras de Ouro:
1. Autonomo - Decisões automáticas
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros
4. Certeiro - Análises precisas 
5. Eficiente - Otimizado
6. Clareza - Bem documentado
7. Modular - Responsabilidade única
8. Plugins - Interface padronizada
9. Testável - Métodos isolados
10. Documentado - Docstrings completos
"""

from utils.logging_config import get_logger

logger = get_logger(__name__)
import time
from typing import Dict, List, Optional
from plugins.plugin import Plugin
from utils.singleton import Singleton


class GerenciadorBot(Plugin, metaclass=Singleton):
    """
    Gerenciador central do bot.

    Responsável por:
    - Coordenar execução dos plugins
    - Gerenciar ciclo de vida do bot
    - Validar dados e resultados
    """

    # Identificadores do plugin
    PLUGIN_NAME = "gerenciador_bot"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.descricao = "Gerenciamento central do bot"
        self._config = None
        self._status = "parado"
        self.timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        self._plugins_ativos: Dict[str, Plugin] = {}
        self.inicializado = False

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o gerenciador.

        Args:
            config: Configurações do bot

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if self.inicializado:
                return True

            # Inicializa classe base primeiro
            if not super().inicializar(config):
                return False

            self._config = config
            self._status = "iniciando"

            # Só marca como inicializado se tudo der certo
            self.inicializado = True
            logger.info(f"Plugin {self.PLUGIN_NAME} inicializado")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador: {e}")
            return False

    def registrar_plugin(self, plugin: Plugin) -> bool:
        """
        Registra um plugin para uso.

        Args:
            plugin: Plugin a ser registrado

        Returns:
            bool: True se registrado com sucesso
        """
        try:
            if not plugin.inicializado:
                logger.error(f"Plugin {plugin.PLUGIN_NAME} não inicializado")
                return False

            self._plugins_ativos[plugin.PLUGIN_NAME] = plugin
            logger.info(f"Plugin {plugin.PLUGIN_NAME} registrado")
            return True

        except Exception as e:
            logger.error(f"Erro ao registrar plugin {plugin.PLUGIN_NAME}: {e}")
            return False

    def _validar_plugins_essenciais(self) -> bool:
        """
        Valida se todos os plugins essenciais estão registrados e ativos.

        Returns:
            bool: True se todos os plugins essenciais estão ok
        """
        plugins_essenciais = {
            "conexao": "Conexão com a Bybit",
            "banco_dados": "Banco de Dados",
            "sinais_plugin": "Gerador de Sinais",
        }

        for nome, descricao in plugins_essenciais.items():
            if nome not in self._plugins_ativos:
                logger.error(f"Plugin essencial faltando: {descricao} ({nome})")
                return False

            if not self._plugins_ativos[nome].inicializado:
                logger.error(f"Plugin não inicializado: {descricao} ({nome})")
                return False

        return True

    def _executar_analises(
        self, dados_ohlcv: list, symbol: str, timeframe: str
    ) -> dict:
        """
        Executa todas as análises disponíveis para um par/timeframe.

        Args:
            dados_ohlcv: Dados OHLCV do par
            symbol: Par de trading
            timeframe: Timeframe da análise

        Returns:
            dict: Resultados das análises
        """
        resultados = {}
        plugins_analise = {
            "analise_candles": "candles",
            "medias_moveis": "medias_moveis",
            "price_action": "price_action",
            "indicadores_tendencia": "tendencia",
        }

        for plugin, chave in plugins_analise.items():
            if plugin in self._plugins_ativos:
                try:
                    if plugin == "indicadores_tendencia":
                        resultados[chave] = self._plugins_ativos[plugin].executar(
                            dados_ohlcv, symbol, timeframe, self._config
                        )
                    else:
                        resultados[chave] = self._plugins_ativos[plugin].executar(
                            dados_ohlcv, symbol, timeframe
                        )
                except Exception as e:
                    logger.error(f"Erro ao executar {plugin}: {e}")

        return resultados

    def executar_ciclo(self) -> bool:
        """
        Executa um ciclo do bot.

        Returns:
            bool: True se ciclo executado com sucesso
        """
        try:
            if self._status != "rodando":
                return True

            # Valida plugins essenciais
            if not self._validar_plugins_essenciais():
                return False

            conexao = self._plugins_ativos["conexao"]
            sinais_plugin = self._plugins_ativos["sinais_plugin"]

            # Obtém apenas pares USDT
            pares_usdt = conexao.obter_pares()
            if not pares_usdt:
                logger.warning("Nenhum par USDT disponível")
                return False

            logger.info(f"Analisando {len(pares_usdt)} pares USDT")

            # Para cada par e timeframe
            for symbol in pares_usdt:
                for timeframe in self.timeframes:
                    try:
                        # Coleta dados OHLCV
                        dados_ohlcv = conexao.obter_klines(symbol, timeframe)
                        if not dados_ohlcv:
                            logger.warning(f"Sem dados para {symbol} {timeframe}")
                            continue

                        # Executa todas as análises disponíveis
                        resultados = self._executar_analises(
                            dados_ohlcv, symbol, timeframe
                        )

                        # Gera sinais se houver resultados
                        if resultados:
                            try:
                                sinais_plugin.executar(resultados, symbol, timeframe)
                            except Exception as e:
                                logger.error(
                                    f"Erro ao gerar sinais para {symbol} {timeframe}: {e}"
                                )

                    except Exception as e:
                        logger.error(f"Erro ao processar {symbol} {timeframe}: {e}")
                        continue

            return True

        except Exception as e:
            logger.error(f"Erro no ciclo: {e}")
            return False

    def iniciar(self) -> bool:
        """
        Inicia execução do bot.

        Returns:
            bool: True se iniciado com sucesso
        """
        try:
            if not self.inicializado:
                logger.error("Gerenciador não inicializado")
                return False

            self._status = "rodando"
            logger.info("Bot iniciado")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}")
            return False

    def parar(self) -> bool:
        """
        Para execução do bot.

        Returns:
            bool: True se parado com sucesso
        """
        try:
            self._status = "parado"
            logger.info("Bot parado")
            return True

        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}")
            return False

    def finalizar(self):
        """Finaliza o gerenciador."""
        try:
            self.parar()
            self._plugins_ativos.clear()
            logger.info("Gerenciador finalizado")

        except Exception as e:
            logger.error(f"Erro ao finalizar gerenciador: {e}")
