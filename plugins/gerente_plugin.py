# plugins/gerente_plugin.py

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

logger = get_logger(__name__)
from typing import Optional, Dict
from plugins.plugin import Plugin
from utils.singleton import singleton


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

            # Lista de plugins essenciais na ordem de carregamento
            plugins_essenciais = [
                "conexao",
                "banco_dados",
                "gerenciador_banco",
                "gerenciador_bot",
            ]

            # Lista de plugins adicionais
            plugins_adicionais = [
                "analise_candles",
                "calculo_alavancagem",
                "calculo_risco",
                "execucao_ordens",
                "medias_moveis",
                "price_action",
                "sinais_plugin",
                "validador_dados",
            ]

            logger.info("Iniciando carregamento de plugins essenciais...")
            for plugin_name in plugins_essenciais:
                logger.debug(f"Tentando carregar plugin essencial: {plugin_name}")
                if not self.carregar_plugin(plugin_name):
                    logger.error(f"Falha ao carregar plugin essencial: {plugin_name}")
                    return False

            logger.info("Iniciando carregamento de plugins adicionais...")
            for plugin_name in plugins_adicionais:
                logger.debug(f"Tentando carregar plugin adicional: {plugin_name}")
                self.carregar_plugin(plugin_name)

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


def obter_conexao():
    """
    Fornece acesso ao plugin de Conexão.

    Returns:
        Conexao: Instância do plugin de Conexão.
    """
    from plugins.conexao import Conexao

    conexao = Conexao()
    return conexao


def obter_banco_dados(config=None):
    """
    Retorna a conexão única com o banco de dados.

    Returns:
        BancoDados: Instância do plugin de banco de dados
    """
    from plugins.banco_dados import BancoDados
    from dotenv import load_dotenv
    import os

    # Carrega variáveis do .env
    load_dotenv()

    # Se não passou config, usa do .env
    if not config:
        config = {
            "database": {
                "host": os.getenv("DB_HOST"),
                "database": os.getenv("DB_NAME"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
            }
        }

    banco = BancoDados()
    banco.inicializar(config)
    return banco


def finalizar_conexao():
    """
    Fecha a conexão com o banco quando o bot for encerrado.
    """
    from plugins.gerenciador_banco import GerenciadorBanco

    gerenciador_banco = GerenciadorBanco()
    gerenciador_banco.fechar_conexao()


def obter_analise_candles():
    """
    Fornece acesso ao plugin de Análise de Candles.

    Returns:
        AnaliseCandles: Instância do plugin de Análise de Candles.
    """
    from plugins.analise_candles import AnaliseCandles

    analise_candles = AnaliseCandles()
    return analise_candles


def obter_calculo_alavancagem():
    """
    Fornece acesso ao plugin de Cálculo de Alavancagem.

    Returns:
        CalculoAlavancagem: Instância do plugin de Cálculo de Alavancagem.
    """
    from plugins.calculo_alavancagem import CalculoAlavancagem

    return CalculoAlavancagem()


def obter_execucao_ordens():
    """
    Fornece acesso ao plugin de Execução de Ordens.

    Returns:
        ExecucaoOrdens: Instância do plugin de Execução de Ordens.
    """
    from plugins.execucao_ordens import ExecucaoOrdens

    execucao_ordens = ExecucaoOrdens()
    return execucao_ordens


def obter_medias_moveis():
    """
    Fornece acesso ao plugin de Médias Móveis.

    Returns:
        MediasMoveis: Instância do plugin de Médias Móveis.
    """
    from plugins.medias_moveis import MediasMoveis

    medias_moveis = MediasMoveis()
    return medias_moveis


def obter_price_action():
    """
    Fornece acesso ao plugin de Price Action.

    Returns:
        PriceAction: Instância do plugin de Price Action.
    """
    from plugins.price_action import PriceAction

    return PriceAction()


def obter_indicadores_osciladores():
    """
    Fornece acesso ao plugin de Indicadores Osciladores.

    Returns:
        IndicadoresOsciladores: Instância do plugin de Indicadores Osciladores.
    """
    from plugins.indicadores.indicadores_osciladores import IndicadoresOsciladores

    indicadores_osciladores = IndicadoresOsciladores()
    return indicadores_osciladores


def obter_indicadores_tendencia():
    """
    Fornece acesso ao plugin de Indicadores de Tendência.

    Returns:
        IndicadoresTendencia: Instância do plugin de Indicadores de Tendência.
    """
    from plugins.indicadores.indicadores_tendencia import IndicadoresTendencia

    indicadores_tendencia = IndicadoresTendencia()
    return indicadores_tendencia


def obter_indicadores_volatilidade():
    """
    Fornece acesso ao plugin de Indicadores de Volatilidade.

    Returns:
        IndicadoresVolatilidade: Instância do plugin de Indicadores de Volatilidade.
    """
    from plugins.indicadores.indicadores_volatilidade import IndicadoresVolatilidade

    indicadores_volatilidade = IndicadoresVolatilidade()
    return indicadores_volatilidade


def obter_indicadores_volume():
    """
    Fornece acesso ao plugin de Indicadores de Volume.

    Returns:
        IndicadoresVolume: Instância do plugin de Indicadores de Volume.
    """
    from plugins.indicadores.indicadores_volume import IndicadoresVolume

    indicadores_volume = IndicadoresVolume()
    return indicadores_volume


def obter_outros_indicadores():
    """
    Fornece acesso ao plugin de Outros Indicadores.

    Returns:
        OutrosIndicadores: Instância do plugin de Outros Indicadores.
    """
    from plugins.indicadores.outros_indicadores import OutrosIndicadores

    outros_indicadores = OutrosIndicadores()
    return outros_indicadores


if __name__ == "__main__":
    gerente = GerentePlugin()
    sucesso = gerente.carregar_plugins("plugins")
    if sucesso:
        print("Plugins carregados:", len(gerente.plugins))
    else:
        print("Falha no carregamento")


# plugins/banco_dados.py
@singleton
class BancoDados(Plugin):
    def __init__(self):
        super().__init__()
        self.nome = "banco_dados"  # Corresponde ao nome do arquivo


# plugins/gerenciador_banco.py
@singleton
class GerenciadorBanco(Plugin):
    def __init__(self):
        super().__init__()
        self.nome = "gerenciador_banco"


# plugins/gerenciador_bot.py
@singleton
class GerenciadorBot(Plugin):
    def __init__(self):
        super().__init__()
        self.nome = "gerenciador_bot"
