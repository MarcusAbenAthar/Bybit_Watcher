# gerenciador_plugins.py
"""Gerenciador de plugins do bot de trading."""

from utils.logging_config import get_logger
import importlib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class GerentePlugin:
    """Gerenciador central de plugins."""

    PLUGINS_ESSENCIAIS = [
        "plugins.conexao",
        "plugins.validador_dados",
        "plugins.sinais_plugin",
        "plugins.analisador_mercado",
        "plugins.calculo_alavancagem",
        "plugins.banco_dados",
        "plugins.gerenciadores.gerenciador_banco",
        "plugins.indicadores.indicadores_tendencia",
        "plugins.indicadores.indicadores_osciladores",
        "plugins.indicadores.indicadores_volatilidade",
        "plugins.indicadores.indicadores_volume",
        "plugins.indicadores.outros_indicadores",
    ]

    def __init__(self):
        """Inicializa o gerenciador."""
        self.plugins = {}
        self._config = None

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o gerenciador com configurações.

        Args:
            config: Dicionário de configurações

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            self._config = config
            return self._carregar_essenciais()
        except Exception as e:
            logger.error(f"Erro ao inicializar GerentePlugin: {e}")
            return False

    def _carregar_essenciais(self) -> bool:
        """Carrega plugins essenciais."""
        for nome in self.PLUGINS_ESSENCIAIS:
            if not self.carregar_plugin(nome):
                logger.error(f"Falha ao carregar plugin essencial {nome}")
                return False
        logger.info("Plugins essenciais carregados")
        return True

    def carregar_plugin(self, nome_plugin: str) -> bool:
        """
        Carrega um plugin dinamicamente.

        Args:
            nome_plugin: Nome do plugin (ex.: "plugins.conexao")

        Returns:
            bool: True se carregado com sucesso
        """
        try:
            if nome_plugin in self.plugins:
                return True

            modulo = importlib.import_module(nome_plugin)
            plugin_class = next(
                (
                    obj
                    for name, obj in vars(modulo).items()
                    if isinstance(obj, type)
                    and issubclass(obj, Plugin)
                    and obj != Plugin
                ),
                None,
            )
            if not plugin_class:
                logger.error(f"Classe Plugin não encontrada em {nome_plugin}")
                return False

            # Instanciação específica pra cada plugin
            if nome_plugin == "plugins.banco_dados":
                gerenciador_banco = self.obter_plugin(
                    "plugins.gerenciadores.gerenciador_banco"
                )
                if not gerenciador_banco:
                    logger.error("GerenciadorBanco não encontrado pra BancoDados")
                    return False
                plugin = plugin_class(gerenciador_banco=gerenciador_banco)
            elif "gerenciador" in nome_plugin:
                plugin = plugin_class()  # Gerenciadores não precisam de gerente
            else:
                plugin = plugin_class(gerente=self)  # Passa gerente por padrão

            if plugin.inicializar(self._config):
                self.plugins[nome_plugin] = plugin
                logger.info(f"Plugin {nome_plugin} carregado")
                return True
            logger.error(f"Falha ao inicializar {nome_plugin}")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar plugin {nome_plugin}: {e}")
            return False

    def obter_plugin(self, nome_plugin: str) -> Plugin | None:
        """
        Obtém um plugin carregado ou tenta carregá-lo.

        Args:
            nome_plugin: Nome do plugin

        Returns:
            Plugin ou None se não encontrado
        """
        if nome_plugin in self.plugins:
            return self.plugins[nome_plugin]
        if self.carregar_plugin(nome_plugin):
            return self.plugins.get(nome_plugin)
        return None

    def finalizar(self) -> None:
        """
        Finaliza todos os plugins carregados.

        Fecha conexões e libera recursos.
        """
        try:
            for nome, plugin in self.plugins.items():
                plugin.finalizar()
                logger.info(f"Plugin {nome} finalizado")
            self.plugins.clear()
            logger.info("GerentePlugin finalizado")
        except Exception as e:
            logger.error(f"Erro ao finalizar GerentePlugin: {e}")
