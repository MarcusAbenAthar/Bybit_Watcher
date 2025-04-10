# gerenciador_plugins.py
# Gerenciador central de plugins registrados via PluginRegistry

from plugins.plugin import Plugin, PluginRegistry
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GerenciadorPlugins:
    """
    Gerenciador central de plugins do sistema.

    - Auto-carrega todos os plugins registrados em PluginRegistry
    - Garante inicialização única e acesso simplificado
    """

    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self._config: dict = {}

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa todos os plugins registrados.

        Args:
            config: Configuração global

        Returns:
            bool: True se todos os plugins essenciais foram inicializados
        """
        self._config = config
        sucesso = True

        for nome_plugin, classe in PluginRegistry.todos().items():
            try:
                plugin = classe(
                    gerente=self
                )  # Plugins recebem o gerente, se necessário
                if plugin.inicializar(config):
                    self.plugins[nome_plugin] = plugin
                    logger.info(f"Plugin carregado: {nome_plugin}")
                else:
                    logger.error(f"Falha ao inicializar plugin: {nome_plugin}")
                    sucesso = False
            except Exception as e:
                logger.error(f"Erro ao instanciar plugin {nome_plugin}: {e}")
                sucesso = False

        return sucesso

    def obter_plugin(self, nome: str) -> Plugin | None:
        """
        Retorna o plugin pelo nome.

        Args:
            nome: Nome do plugin (PLUGIN_NAME)

        Returns:
            Plugin ou None
        """
        plugin = self.plugins.get(nome)
        if not plugin:
            logger.warning(f"Plugin '{nome}' não encontrado.")
        return plugin

    def finalizar(self) -> None:
        """Finaliza todos os plugins carregados."""
        for nome, plugin in self.plugins.items():
            try:
                plugin.finalizar()
                logger.info(f"Plugin finalizado: {nome}")
            except Exception as e:
                logger.error(f"Erro ao finalizar plugin {nome}: {e}")
        self.plugins.clear()
