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


logger = get_logger(__name__)


class GerentePlugin:
    """Gerenciador central de plugins."""

    def __init__(self):
        """Inicializa o gerenciador."""
        self.plugins: Dict[str, Plugin] = {}
        self.config = None
        self.initialized = False
        self.gerenciador_banco = None  # Armazena a instância do gerenciador de banco

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
        try:
            nome_plugin = nome_plugin.replace("plugins.", "").replace("/", ".")
            nome_base = nome_plugin.split(".")[-1]
            if nome_base in self.plugins:
                return True

            modulo = importlib.import_module(f"plugins.{nome_plugin}")

            plugin_class = None
            for name, obj in vars(modulo).items():
                if isinstance(obj, type) and issubclass(obj, Plugin) and obj != Plugin:
                    plugin_class = obj
                    break

            if not plugin_class:
                logger.error(f"Nenhuma classe plugin encontrada em {nome_plugin}")
                return False

            # Injeção de dependência para banco_dados
            if nome_base == "banco_dados":
                if self.gerenciador_banco is None:
                    logger.error(
                        "Gerenciador de banco não carregado. Carregue-o antes de banco_dados"
                    )
                    return False
                plugin = plugin_class(gerenciador_banco=self.gerenciador_banco)
            else:
                plugin = plugin_class()
            
            if not plugin.inicializar(self.config):
                logger.error(f"Falha ao inicializar {nome_plugin}")
                return False

            self.plugins[nome_base] = plugin
            # Armazena a instancia do gerenciador de banco
            if nome_base == "gerenciador_banco":
                self.gerenciador_banco = plugin

            logger.info(f"Plugin %s carregado com sucesso", nome_base)
            return True
        except Exception as e:
            logger.exception(
                f"Erro ao carregar plugin {nome_plugin}: {e}"
            )  # Log full traceback
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
            "gerenciador_banco": "Gerenciador do Banco",
            "banco_dados": "Banco de Dados",
            "conexao": "Conexão com a Bybit",
            "gerenciador_bot": "Gerenciador do Bot",
        }

        for nome, descricao in essenciais.items():
            # Extrai o nome base do plugin
            nome_base = nome.split(".")[-1]
            if nome_base not in self.plugins:
                logger.error(f"Plugin essencial faltando: {descricao} ({nome})")
                return False

            if not self.plugins[nome_base].inicializado:
                logger.error(f"Plugin não inicializado: {descricao} ({nome})")
                return False

        return True

    def executar_ciclo(self, dados, symbol, timeframe, config) -> bool:
        try:
            for plugin in self.plugins.values():
                if not plugin.executar(dados, symbol, timeframe, config):
                    logger.error(f"Erro na execução do plugin: {plugin.nome}")
                    return False
            return True
        except Exception as e:
            logger.exception(
                f"Erro no ciclo: {e}"
            )  # Use logger.exception for full traceback
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


def obter_calculo_alavancagem():
    """
    Retorna a instância do plugin CalculoAlavancagem.
    """
    from plugins.calculo_alavancagem import CalculoAlavancagem

    return CalculoAlavancagem()
