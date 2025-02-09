# plugins/gerente_plugin.py

"""
Gerenciador de plugins para o bot de trading.

Este módulo é responsável por carregar e fornecer acesso aos plugins do bot,
seguindo as Regras de Ouro para garantir a clareza, modularidade e 
testabilidade do código.

"""

import os
import importlib
import logging
from plugins.plugin import Plugin

logger = logging.getLogger(__name__)


class GerentePlugin:
    def __init__(self):
        self.plugins = {}

    def inicializar(self, config):
        """Inicializa o gerente de plugins com a configuração fornecida."""
        self.config = config

    def carregar_plugins(self, caminho_plugins: str, config=None) -> bool:
        """Carrega plugins apenas se ainda não foram carregados."""
        if self.plugins:
            logger.info("Plugins já carregados anteriormente")
            return True

        try:
            plugins_carregados = []

            if os.path.isdir(caminho_plugins):
                arquivos = os.listdir(caminho_plugins)
            else:
                arquivos = [caminho_plugins]

            for arquivo in arquivos:
                if self._eh_plugin_valido(arquivo):
                    nome_modulo = os.path.splitext(os.path.basename(arquivo))[
                        0
                    ]  # Remove .py
                    plugin = self._carregar_plugin(nome_modulo, config)

                    if plugin:
                        plugins_carregados.append(plugin)
                        self.plugins[nome_modulo] = plugin
                        logger.info(f"Plugin carregado: {plugin.nome}")

            if not plugins_carregados:
                logger.warning("Nenhum plugin foi carregado")
                return False

            logger.info(f"Total de plugins carregados: {len(plugins_carregados)}")
            return True

        except Exception as e:
            logger.error(f"Erro no carregamento de plugins: {e}")
            return False

    def _carregar_plugin(self, nome_modulo: str, config=None):
        """Carrega um plugin específico."""
        try:
            modulo = importlib.import_module(f"plugins.{nome_modulo}")
            for nome_item in dir(modulo):
                item = getattr(modulo, nome_item)
                if (
                    isinstance(item, type)
                    and issubclass(item, Plugin)
                    and item != Plugin
                ):
                    instancia = item()
                    instancia.inicializar(config)
                    return instancia
            return None
        except Exception as e:
            logger.error(f"Erro ao carregar módulo {nome_modulo}: {e}")
            return None

    def _eh_plugin_valido(self, arquivo: str) -> bool:
        """Verifica se o arquivo é um plugin válido."""
        return arquivo.endswith(".py") and not arquivo.startswith("__")

    def verificar_plugins_essenciais(self) -> bool:
        """Verifica se todos os plugins essenciais estão carregados."""
        for plugin in ["conexao", "banco_dados", "gerenciador_bot"]:
            if plugin not in self.plugins:
                logger.error(f"Plugin essencial não carregado: {plugin}")
                return False
        return True


def inicializar_banco_dados(config):
    """
    Inicializa o banco de dados e cria as tabelas.
    """
    logger.debug("Inicializando banco de dados...")

    conectar_banco_dados(config)
    banco_dados = obter_banco_dados(config)

    # Cria o banco de dados
    banco_dados.criar_banco_dados(
        config.get("database", "database"),
        config.get("database", "user"),
        config.get("database", "password"),
    )

    # Conecta ao banco de dados
    banco_dados.conectar(
        config.get("database", "database"),
        config.get("database", "user"),
        config.get("database", "password"),
        config.get("database", "host"),
    )
    # Cria as tabelas
    banco_dados.criar_tabela("klines")
    banco_dados.criar_tabela("analise_candles")
    banco_dados.criar_tabela("medias_moveis")
    banco_dados.criar_tabela("indicadores_osciladores")
    banco_dados.criar_tabela("indicadores_tendencia")
    banco_dados.criar_tabela("indicadores_volatilidade")
    banco_dados.criar_tabela("indicadores_volume")
    banco_dados.criar_tabela("outros_indicadores")

    logger.debug(
        "Banco de dados inicializado com sucesso!"
    )  # Adiciona um log no final da função


def conectar_banco_dados(config):
    """
    Conecta ao banco de dados usando o plugin BancoDados.

    Args:
        config (ConfigParser): Objeto com as configurações do bot.
    """
    try:
        # Obtém a instância da classe BancoDados
        banco_dados = obter_banco_dados(config)

        # Obtém as configurações do objeto config
        db_host = config.get("database", "host")
        db_name = config.get("database", "database")
        db_user = config.get("database", "user")
        db_password = config.get("database", "password")

        # Conecta ao banco de dados
        banco_dados.conectar(db_name, db_user, db_password, db_host)

    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise


def armazenar_dados(config, dados, symbol, timeframe):
    """
    Armazena os dados no banco de dados usando o plugin BancoDados.

    Args:
        config (ConfigParser): Objeto com as configurações do bot.
        dados (list): Lista de dados a serem armazenados.
        symbol (str): Par de moedas.
        timeframe (str): Timeframe dos dados.
    """
    try:
        banco_dados = obter_banco_dados()
        banco_dados.inserir_dados(
            "klines",
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "dados": dados,
            },
        )
    except Exception as e:
        logger.error(f"Erro ao armazenar dados: {e}")


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
    """
    from plugins.gerenciador_banco import gerenciador_banco

    if config:
        gerenciador_banco.inicializar(config)
    return gerenciador_banco.get_conexao()


def finalizar_conexao():
    """
    Fecha a conexão com o banco quando o bot for encerrado.
    """
    from plugins.gerenciador_banco import gerenciador_banco

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
