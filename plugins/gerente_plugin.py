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
from typing import Optional, Dict
from utils.singleton import singleton
from utils.logging_config import get_logger
from plugins.plugin import Plugin

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

    def carregar_plugins(self, caminho_plugins: str) -> bool:
        """
        Carrega plugins do diretório especificado.

        Args:
            caminho_plugins: Caminho para o diretório de plugins

        Returns:
            bool: True se plugins carregados com sucesso
        """
        try:
            # Log do diretório base
            caminho_base = os.path.abspath(caminho_plugins)
            logger.info(f"Buscando plugins em: {caminho_base}")

            # Lista de plugins em ordem de dependência
            plugins_ordem = {
                # Nível 1 - Infraestrutura básica
                1: ["conexao", "gerenciador_banco"],
                
                # Nível 2 - Gerenciamento de dados
                2: ["banco_dados", "validador_dados"],
                
                # Nível 3 - Gerenciamento central
                3: ["gerenciador_bot"],
                
                # Nível 4 - Análise técnica básica
                4: [
                    "analise_candles",
                    "medias_moveis",
                    "price_action"
                ],
                
                # Nível 5 - Indicadores
                5: [
                    "indicadores/indicadores_tendencia",
                    "indicadores/indicadores_osciladores",
                    "indicadores/indicadores_volatilidade",
                    "indicadores/indicadores_volume",
                    "indicadores/outros_indicadores"
                ],
                
                # Nível 6 - Análise avançada
                6: [
                    "calculo_risco",
                    "calculo_alavancagem"
                ],
                
                # Nível 7 - Geração de sinais
                7: ["sinais_plugin"]
            }

            # Carrega plugins em ordem
            for nivel in sorted(plugins_ordem.keys()):
                logger.info(f"Carregando plugins nível {nivel}...")
                plugins_nivel = plugins_ordem[nivel]
                
                for plugin_name in plugins_nivel:
                    logger.debug(f"Tentando carregar plugin: {plugin_name}")
                    
                    # Plugins de nível 1-3 são essenciais
                    if nivel <= 3:
                        if not self.carregar_plugin(plugin_name):
                            logger.error(f"Falha ao carregar plugin essencial: {plugin_name}")
                            return False
                    else:
                        self.carregar_plugin(plugin_name)

            # Verifica plugins essenciais
            if not self.verificar_plugins_essenciais():
                logger.error("Falha na verificação de plugins essenciais")
                return False

            if not self.plugins:
                logger.warning("Nenhum plugin carregado")
                return False

            logger.info(f"Total de plugins carregados: {len(self.plugins)}")
            return True

        except Exception as e:
            logger.error(f"Erro ao carregar plugins: {e}")
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
            logger.debug(f"carregar_plugin chamado com {nome_plugin}")
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

                # Primeiro verifica se é uma classe e herda de Plugin
                if not (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr != Plugin
                ):
                    continue

                logger.debug(f"Encontrada classe que herda de Plugin: {attr_name}")

                # Log detalhado da classe sendo inspecionada
                logger.debug(f"Inspecionando classe: {attr_name}")
                logger.debug(f"Herda de Plugin: {issubclass(attr, Plugin)}")

                # Verifica atributos PLUGIN_NAME e PLUGIN_TYPE
                if hasattr(attr, "PLUGIN_NAME") and hasattr(attr, "PLUGIN_TYPE"):
                    plugin_name = getattr(attr, "PLUGIN_NAME", "").lower()
                    plugin_type = getattr(attr, "PLUGIN_TYPE", "").lower()
                    logger.debug(
                        f"PLUGIN_NAME={plugin_name}, PLUGIN_TYPE={plugin_type}"
                    )
                    logger.debug(f"Comparando com nome_plugin={nome_plugin.lower()}")

                    # Verifica correspondência exata com nome do plugin
                    if plugin_name == nome_plugin.lower():
                        logger.info(f"Plugin encontrado via PLUGIN_NAME: {attr_name}")
                        plugin_class = attr
                        break
                else:
                    logger.debug(
                        f"Classe {attr_name} não tem PLUGIN_NAME ou PLUGIN_TYPE"
                    )

                # Se não encontrou por PLUGIN_NAME, tenta pelo nome da classe
                if not plugin_class:
                    class_name = attr_name.lower()
                    if class_name == nome_plugin.lower():
                        logger.info(
                            f"Plugin encontrado via nome da classe: {attr_name}"
                        )
                        plugin_class = attr
                        break

                    # Converte CamelCase para snake_case como última tentativa
                    snake_case = "".join(
                        [
                            "_" + c.lower() if c.isupper() else c.lower()
                            for c in attr_name
                        ]
                    ).lstrip("_")
                    if snake_case == nome_plugin.lower():
                        logger.info(f"Plugin encontrado via snake_case: {attr_name}")
                        plugin_class = attr
                        break

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


if __name__ == "__main__":
    gerente = GerentePlugin()
    sucesso = gerente.carregar_plugins("plugins")
    if sucesso:
        print("Plugins carregados:", len(gerente.plugins))
    else:
        print("Falha no carregamento")