"""
Gerenciador de plugins para o bot de trading.

Regras de Ouro:
1. Autonomo - Gerencia plugins de forma independente
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros
4. Certeiro - Verificações precisas
5. Eficiente - Carregamento otimizado
6. Clareza - Bem documentado
7. Modular - Responsabilidade única
8. Plugins - Sistema dinâmico
9. Testável - Métodos isolados
10. Documentado - Docstrings completos
"""

import os
import importlib
from utils.logging_config import get_logger
from typing import Optional, Dict
from plugins.plugin import Plugin
from utils.singleton import singleton

logger = get_logger(__name__)


@singleton
class GerentePlugin:
    """Gerenciador central de plugins."""

    def __init__(self):
        """Inicializa o gerenciador."""
        self.plugins: Dict[str, Plugin] = {}
        self.config = None
        self.initialized = False

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o gerenciador com configurações.

        Args:
            config: Configurações do sistema

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            self.config = config
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar gerente: {e}")
            return False

    def carregar_plugin(self, nome_plugin: str) -> bool:
        """
        Carrega um plugin específico.

        Args:
            nome_plugin: Nome do plugin a ser carregado

        Returns:
            bool: True se carregado com sucesso
        """
        try:
            # Remove 'plugins.' do nome se presente
            nome_plugin = nome_plugin.replace("plugins.", "")

            if nome_plugin in self.plugins:
                logger.debug(f"Plugin {nome_plugin} já carregado")
                return True

            # Log do caminho completo
            caminho_modulo = f"plugins.{nome_plugin}"
            logger.info(f"Tentando importar módulo: {caminho_modulo}")

            # Importa módulo
            try:
                modulo = importlib.import_module(caminho_modulo)
                caminho_arquivo = os.path.abspath(modulo.__file__)
                logger.info(f"Módulo {nome_plugin} importado de: {caminho_arquivo}")
            except ImportError as e:
                logger.error(f"Falha ao importar {nome_plugin}: {e}")
                return False

            # Busca classe do plugin
            plugin_class = None
            for attr_name in dir(modulo):
                attr = getattr(modulo, attr_name)

                # Verifica se é uma classe que herda de Plugin
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr != Plugin
                ):
                    # Tenta instanciar para verificar o nome
                    try:
                        instance = attr()
                        if (
                            hasattr(instance, "nome")
                            and instance.nome.lower() == nome_plugin.lower()
                        ):
                            plugin_class = attr
                            logger.debug(
                                f"Classe plugin válida encontrada: {attr_name}"
                            )
                            break  # Encontrou a classe, pode sair do loop
                    except Exception as e:
                        logger.error(f"Erro ao instanciar {attr_name}: {e}")
                        continue

            if not plugin_class:
                logger.warning(f"Nenhuma classe plugin encontrada em {nome_plugin}")
                return False

            # Instancia o plugin
            plugin = plugin_class()

            # Inicializa o plugin
            if self.config and not plugin.inicializar(self.config):
                logger.error(f"Falha ao inicializar {nome_plugin}")
                return False

            self.plugins[nome_plugin] = plugin
            logger.info(f"Plugin {nome_plugin} carregado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao carregar plugin {nome_plugin}: {e}", exc_info=True)
            return False

    def _carregar_plugin(self, nome_modulo: str) -> Optional[Plugin]:
        """
        Carrega um plugin específico.

        Args:
            nome_modulo: Nome do módulo do plugin (sem .py)

        Returns:
            Optional[Plugin]: Instância do plugin ou None se falhar
        """
        try:
            # Importa o módulo
            modulo = importlib.import_module(f"plugins.{nome_modulo}")

            # Procura pela classe que herda de Plugin
            for item_name in dir(modulo):
                item = getattr(modulo, item_name)

                # Verifica se é uma classe que herda de Plugin
                if (
                    isinstance(item, type)
                    and issubclass(item, Plugin)
                    and item != Plugin
                ):

                    # Instancia o plugin
                    plugin = item()

                    # Verifica se o nome corresponde
                    if plugin.nome == nome_modulo:
                        # Inicializa o plugin
                        if self.config:
                            plugin.inicializar(self.config)

                        logger.info(f"Plugin {nome_modulo} carregado com sucesso")
                        return plugin

            logger.warning(f"Plugin {nome_modulo} não encontrado")
            return None

        except ImportError as e:
            logger.error(f"Erro ao importar plugin {nome_modulo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao carregar plugin {nome_modulo}: {e}")
            return None

    def _eh_plugin_valido(self, arquivo: str) -> bool:
        """
        Verifica se arquivo é um plugin válido.

        Args:
            arquivo: Nome do arquivo

        Returns:
            bool: True se for plugin válido
        """
        return arquivo.endswith(".py") and not arquivo.startswith("__")

    def verificar_plugins_essenciais(self) -> bool:
        """
        Verifica se plugins essenciais estão carregados.

        Returns:
            bool: True se todos plugins essenciais OK
        """
        essenciais = {
            "conexao": "Conexão com a Bybit",
            "banco_dados": "Banco de Dados",
            "gerenciador_banco": "Gerenciador do Banco",
            "gerenciador_bot": "Gerenciador do Bot",
        }

        for nome, descricao in essenciais.items():
            if nome not in self.plugins:
                logger.error(f"Plugin essencial faltando: {descricao} ({nome})")
                return False

            if not self.plugins[nome].inicializado:
                logger.error(f"Plugin não inicializado: {descricao} ({nome})")
                return False

        return True

    def executar_ciclo(self) -> bool:
        """
        Executa um ciclo em todos os plugins.

        Returns:
            bool: True se ciclo executado com sucesso
        """
        try:
            for plugin in self.plugins.values():
                if not plugin.executar():
                    return False
            return True
        except Exception as e:
            logger.error(f"Erro no ciclo: {e}")
            return False

    def finalizar(self):
        """Finaliza todos os plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.finalizar()
            except Exception as e:
                logger.error(f"Erro ao finalizar {plugin.nome}: {e}")

    def listar_plugins(self) -> None:
        """Lista todos os plugins carregados."""
        try:
            logger.info("=== Plugins Carregados ===")
            if not self.plugins:
                logger.warning("Nenhum plugin carregado!")
                return

            for nome, plugin in self.plugins.items():
                status = "✓" if plugin.inicializado else "✗"
                logger.info(f"{status} {nome}: {plugin.descricao}")

            logger.info(f"Total de plugins: {len(self.plugins)}")

        except Exception as e:
            logger.error(f"Erro ao listar plugins: {e}")
