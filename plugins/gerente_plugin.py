# plugins/gerente_plugin.py

"""
Gerenciador de plugins para o bot de trading.

Este módulo é responsável por carregar e fornecer acesso aos plugins do bot,
seguindo as Regras de Ouro para garantir a clareza, modularidade e 
testabilidade do código.

"""

from plugins.plugin import Plugin
import logging

logger = logging.getLogger(__name__)
import os
import importlib


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


def carregar_plugins(diretorio, config=None):
    """
    Carrega todos os plugins de um determinado diretório.

    Args:
        diretorio: Caminho para o diretório de plugins
        config: Configurações para os plugins

    Returns:
        list: Lista de instâncias dos plugins carregados
    """
    plugins = []
    logger.debug(f"=== Iniciando carregamento de plugins ===")

    try:
        # Lista todos os arquivos .py no diretório
        arquivos = [
            f
            for f in os.listdir(diretorio)
            if f.endswith(".py") and not f.startswith("_")
        ]

        # Ordena os arquivos para garantir ordem de carregamento
        ordem_plugins = [
            "indicadores_tendencia.py",
            "medias_moveis.py",
            "sinais_plugin.py",
        ]

        # Coloca os plugins prioritários no início
        for plugin_nome in ordem_plugins:
            if plugin_nome in arquivos:
                arquivos.remove(plugin_nome)
                arquivos.insert(0, plugin_nome)

        # Carrega cada plugin
        for arquivo in arquivos:
            nome_modulo = arquivo[:-3]  # Remove .py
            try:
                # Importa o módulo
                modulo = importlib.import_module(f"{diretorio}.{nome_modulo}")

                # Procura pela classe do plugin
                for nome_attr in dir(modulo):
                    attr = getattr(modulo, nome_attr)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Plugin)
                        and attr != Plugin
                    ):

                        # Instancia o plugin com config se necessário
                        if "config" in attr.__init__.__code__.co_varnames:
                            plugin = attr(config)
                        else:
                            plugin = attr()

                        plugins.append(plugin)
                        logger.debug(f"Plugin carregado com sucesso: {nome_attr}")

            except Exception as e:
                logger.error(f"Erro ao carregar plugin {nome_modulo}: {e}")

        logger.debug(f"=== Total de plugins carregados: {len(plugins)} ===")
        for p in plugins:
            logger.debug(f"Plugin ativo: {p.__class__.__name__}")

    except Exception as e:
        logger.error(f"Erro ao carregar plugins: {e}")

    return plugins


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


def obter_banco_dados(config):
    """
    Fornece acesso ao plugin de Banco de Dados.

    Returns:
        BancoDados: Instância do plugin de Banco de Dados.
    """
    from plugins.banco_dados import BancoDados

    # Cria a instância da classe BancoDados
    banco_dados = BancoDados(config)

    return banco_dados


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

    calculo_alavancagem = CalculoAlavancagem()
    return calculo_alavancagem  # Retorna a instância da classe CalculoAlavancagem


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
