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
from utils.singleton import singleton


@singleton
class GerenciadorBot(Plugin):
    """
    Gerenciador central do bot.

    Responsável por:
    - Coordenar execução dos plugins
    - Gerenciar ciclo de vida do bot
    - Validar dados e resultados
    """

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self.nome = "gerenciador_bot"
        self.descricao = "Gerenciamento central do bot"
        self._config = None
        self._status = "parado"
        self.inicializado = False
        self.timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        self._plugins_ativos: Dict[str, Plugin] = {}

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

            self._config = config
            self._status = "iniciando"
            self.inicializado = True
            logger.info(f"Plugin {self.nome} inicializado")
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
                logger.error(f"Plugin {plugin.nome} não inicializado")
                return False

            self._plugins_ativos[plugin.nome] = plugin
            logger.info(f"Plugin {plugin.nome} registrado")
            return True

        except Exception as e:
            logger.error(f"Erro ao registrar plugin {plugin.nome}: {e}")
            return False

    def executar_ciclo(self) -> bool:
        """
        Executa um ciclo do bot.

        Returns:
            bool: True se ciclo executado com sucesso
        """
        try:
            if self._status != "rodando":
                return True

            # Executa plugins na ordem correta
            ordem_execucao = [
                "conexao",
                "banco_dados",
                "analise_candles",
                "indicadores_tendencia",
                "indicadores_osciladores",
                "indicadores_volatilidade",
                "indicadores_volume",
                "medias_moveis",
                "price_action",
                "sinais_plugin",
            ]

            for nome_plugin in ordem_execucao:
                if nome_plugin in self._plugins_ativos:
                    plugin = self._plugins_ativos[nome_plugin]
                    if not plugin.executar():
                        logger.error(f"Falha ao executar {nome_plugin}")
                        return False

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
