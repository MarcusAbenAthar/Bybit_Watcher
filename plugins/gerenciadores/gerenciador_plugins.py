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

    # Plugins essenciais com suas descrições
    PLUGINS_ESSENCIAIS = [
        ("plugins.validador_dados", "Validador de Dados"),
        ("plugins.gerenciadores.gerenciador_banco", "Gerenciador do Banco"),
        ("plugins.banco_dados", "Banco de Dados"),
        ("plugins.conexao", "Conexão com a Bybit"),
        ("plugins.sinais_plugin", "Gerador de Sinais"),
        ("plugins.analisador_mercado", "Analisador de Mercado"),
        ("plugins.gerenciadores.gerenciador_bot", "Gerenciador do Bot"),
        ("plugins.calculo_alavancagem", "Cálculo de Alavancagem"),
    ]

    # Plugins que precisam do validador_dados
    PLUGINS_COM_VALIDADOR = ["calculo_risco", "calculo_alavancagem"]

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

    def _gerar_plugin_key(self, nome_plugin: str) -> str:
        """Gera uma chave consistente para o plugin."""
        if not nome_plugin.startswith("plugins."):
            nome_plugin = f"plugins.{nome_plugin}"
        return nome_plugin.replace("/", ".")

    def _plugin_ja_carregado(self, plugin_key: str) -> bool:
        """Verifica se um plugin já está carregado usando sua chave."""
        return plugin_key in self.plugins and self.plugins[plugin_key].inicializado

    def carregar_plugin(self, nome_plugin: str) -> bool:
        """Carrega um plugin e suas dependências."""
        try:
            # Gera chave consistente para o plugin
            plugin_key = self._gerar_plugin_key(nome_plugin)

            # Verifica se já está carregado
            if self._plugin_ja_carregado(plugin_key):
                logger.debug(f"Plugin {plugin_key} já carregado e inicializado")
                return True
            # Importa o módulo
            try:
                modulo = importlib.import_module(plugin_key)
            except ImportError as e:
                logger.error(f"Erro ao importar módulo {plugin_key}: {e}")
                return False

            # Encontra a classe do plugin (primeira classe que herda de Plugin)
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
                logger.error(f"Nenhuma classe plugin encontrada em {plugin_key}")
                return False

            # Determina o nome do plugin
            if hasattr(plugin_class, "PLUGIN_NAME") and plugin_class.PLUGIN_NAME:
                plugin_name = plugin_class.PLUGIN_NAME
            elif plugin_key.startswith("plugins.indicadores."):
                # Para plugins de indicadores, usa o nome da classe
                plugin_name = plugin_class.__name__
            else:
                # Para outros plugins, usa a última parte do caminho
                plugin_name = plugin_key.split(".")[-1]

            # Cria instância do plugin com tratamento especial por tipo
            try:
                plugin = self._criar_plugin_especifico(
                    plugin_class, plugin_name, plugin_key
                )
                if not plugin:
                    return False

                # Configura e inicializa o plugin
                if not self._configurar_e_inicializar_plugin(
                    plugin, plugin_name, plugin_key
                ):
                    return False

                logger.info(
                    f"Plugin {plugin_name} carregado e inicializado com sucesso"
                )
                return True

            except Exception as e:
                logger.error(f"Erro ao criar/configurar plugin {plugin_name}: {e}")
                return False
        except Exception as e:
            logger.exception(
                f"Erro ao carregar plugin {nome_plugin}: {e}"
            )  # Log full traceback
            return False

    def obter_banco_dados(self):
        """
        Retorna a instância do plugin BancoDados.
        """
        from plugins.banco_dados import BancoDados

        # Cria e inicializa o banco de dados
        banco = BancoDados(self.gerenciador_banco)
        if not banco.inicializar(self.config):
            logger.error("Falha ao inicializar banco de dados")
            return None

        return banco

    def _criar_plugin_especifico(
        self, plugin_class, plugin_name: str, plugin_key: str
    ) -> Optional[Plugin]:
        """Cria uma instância específica do plugin com base em seu tipo."""
        try:
            # Plugins básicos que não precisam de parâmetros
            if plugin_name in ["validador_dados"]:
                return plugin_class()

            # Plugins que precisam apenas do gerenciador de banco
            if plugin_name == "banco_dados":
                # Garante que o gerenciador_banco existe
                if not self.gerenciador_banco:
                    logger.info("Carregando gerenciador_banco para banco_dados")
                    gerenciador = self.obter_plugin("gerenciadores.gerenciador_banco")
                    if not gerenciador:
                        logger.error("Falha ao obter gerenciador_banco")
                        return None
                    self.gerenciador_banco = gerenciador

                # Garante que está inicializado
                if not self.gerenciador_banco.inicializado:
                    if not self.gerenciador_banco.inicializar(self.config):
                        logger.error("Falha ao inicializar gerenciador_banco")
                        return None

                # Cria o banco_dados com o gerenciador inicializado
                plugin = plugin_class(gerenciador_banco=self.gerenciador_banco)
                if not plugin:
                    logger.error("Falha ao criar banco_dados")
                    return None

                return plugin

            # Plugins que precisam do gerente e config
            if (
                plugin_key.startswith("plugins.indicadores.")
                or plugin_name == "analise_candles"
            ):
                return plugin_class(gerente=self, config=self.config)

            # AnalisadorMercado precisa apenas do gerente
            if plugin_name == "analisador_mercado":
                # Carrega suas dependências primeiro
                plugins_analise = [
                    "plugins.analise_candles",
                    "plugins.medias_moveis",
                    "plugins.price_action",
                    "plugins.indicadores.indicadores_tendencia",
                ]
                for plugin_dep in plugins_analise:
                    if not self._carregar_dependencia(plugin_dep):
                        logger.error(f"Falha ao carregar dependência {plugin_dep}")
                        return None

                return plugin_class(gerente=self)

            # Gerenciador bot é um caso especial
            if plugin_name == "gerenciador_bot":
                # Garante que todos os plugins essenciais estejam carregados
                for nome, _ in self.PLUGINS_ESSENCIAIS:
                    if nome != "plugins.gerenciadores.gerenciador_bot":
                        if not self._plugin_ja_carregado(nome):
                            if not self.carregar_plugin(nome):
                                logger.error(
                                    f"Falha ao carregar plugin essencial {nome}"
                                )
                                return None

                gerenciador = plugin_class()
                # Inicializa primeiro para poder registrar os plugins
                if not gerenciador.inicializar(self.config):
                    return None
                # Registra plugins já carregados
                for nome, plugin in self.plugins.items():
                    gerenciador.registrar_plugin(plugin)
                return gerenciador

            # Plugins que não recebem parâmetros no construtor
            if plugin_name in [
                "conexao",
                "calculo_risco",
                "execucao_ordens",
                "medias_moveis",
                "price_action",
                "sinais_plugin",
            ]:
                return plugin_class()

            # Gerenciador de banco é um caso especial
            if plugin_name == "gerenciador_banco":
                plugin = plugin_class()
                self.gerenciador_banco = plugin
                return plugin

            # Plugins que precisam apenas do config
            if plugin_name in ["calculo_alavancagem"]:
                return plugin_class(self.config)

            # Se não souber como criar, não passa parâmetros
            return plugin_class()

        except Exception as e:
            logger.error(f"Erro ao criar plugin {plugin_name}: {e}")
            return None

    def _configurar_e_inicializar_plugin(
        self, plugin: Plugin, plugin_name: str, plugin_key: str
    ) -> bool:
        """Configura e inicializa um plugin."""
        try:
            # Configura dependências especiais
            if plugin_name in ["calculo_risco", "calculo_alavancagem"]:
                validador_dados = self._obter_validador_dados()
                if not validador_dados:
                    return False
                plugin._validador = validador_dados

            # Armazena o plugin com a chave já gerada
            self.plugins[plugin_key] = plugin

            # Inicializa o plugin
            if not plugin.inicializar(self.config):
                logger.error(f"Falha ao inicializar {plugin_name}")
                del self.plugins[plugin_key]
                return False

            return True

        except Exception as e:
            logger.error(f"Erro ao configurar/inicializar plugin {plugin_name}: {e}")
            return False

    def _carregar_dependencia(self, nome_dependencia: str) -> bool:
        """Carrega uma dependência se ainda não estiver carregada."""
        plugin_key = self._gerar_plugin_key(nome_dependencia)
        if not self._plugin_ja_carregado(plugin_key):
            if not self.carregar_plugin(nome_dependencia):
                logger.error(f"Falha ao carregar dependência {nome_dependencia}")
                return False
        return True

    def obter_plugin(self, nome_plugin: str) -> Optional[Plugin]:
        """
        Obtém ou carrega um plugin.

        Args:
            nome_plugin: Nome do plugin a ser obtido

        Returns:
            Optional[Plugin]: Instância do plugin ou None se falhar
        """
        plugin_key = self._gerar_plugin_key(nome_plugin)
        plugin = self.plugins.get(plugin_key)
        if not plugin or not plugin.inicializado:
            logger.info(f"Carregando plugin {nome_plugin}")
            if not self.carregar_plugin(nome_plugin):
                logger.error(f"Falha ao carregar plugin {nome_plugin}")
                return None
            plugin = self.plugins[plugin_key]
            if not plugin.inicializado:
                logger.error(f"Plugin {nome_plugin} não está inicializado")
                return None
        return plugin

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
        # Força o carregamento do validador_dados primeiro
        validador_dados = self._obter_validador_dados()
        if not validador_dados:
            logger.error("Falha ao carregar validador_dados")
            return False
        logger.info("Validador de dados carregado com sucesso")

        # Verifica plugins essenciais na ordem definida
        for nome, descricao in self.PLUGINS_ESSENCIAIS:
            if nome not in self.plugins:
                logger.error(f"Plugin essencial faltando: {descricao} ({nome})")
                if not self.carregar_plugin(nome):
                    logger.error(f"Falha ao carregar plugin {nome}")
                    return False
                logger.info(f"Plugin {nome} carregado com sucesso")

            plugin = self.plugins[nome]
            if not plugin.inicializado:
                logger.error(f"Plugin não inicializado: {descricao} ({nome})")
                if not plugin.inicializar(self.config):
                    logger.error(f"Falha ao reinicializar {nome}")
                    return False
                logger.info(f"Plugin {nome} reinicializado com sucesso")

        return True

    def executar_ciclo(self, dados, symbol, timeframe, config) -> bool:
        """Executa o ciclo em todos os plugins carregados."""
        try:
            kwargs = {
                "dados": dados,
                "symbol": symbol,
                "timeframe": timeframe,
                "config": config,
            }
            for plugin in self.plugins.values():
                if not plugin.executar(**kwargs):
                    logger.error(f"Erro na execução do plugin: {plugin.nome}")
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

    def _obter_validador_dados(self) -> Optional[Plugin]:
        """Obtém ou carrega o validador_dados."""
        return self.obter_plugin("validador_dados")

    def obter_calculo_alavancagem(self) -> Optional[Plugin]:
        """Obtém a instância do plugin de cálculo de alavancagem."""
        return self.obter_plugin("calculo_alavancagem")

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


# Função removida pois criava instâncias duplicadas.
# Agora o plugin é obtido diretamente do gerenciador através de self.plugins
