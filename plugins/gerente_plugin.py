# plugins/gerente_plugin.py

"""
Gerenciador de plugins para o bot de trading.

Este módulo é responsável por carregar e fornecer acesso aos plugins do bot,
seguindo as Regras de Ouro para garantir a clareza, modularidade e testabilidade do código.
"""

from plugins.plugin import Plugin
from loguru import logger
import os
import importlib


def carregar_plugins(diretorio):
    """
    Carrega todos os plugins de um determinado diretório.

    Args:
        diretorio (str): Caminho para o diretório onde os plugins estão localizados.

    Returns:
        list: Uma lista com os plugins carregados.
    """
    plugins = []
    for nome_arquivo in os.listdir(diretorio):
        if nome_arquivo.endswith(".py") and not nome_arquivo.startswith("_"):
            nome_modulo = nome_arquivo[:-3]
            try:
                modulo = importlib.import_module(f"{diretorio}.{nome_modulo}")
                for nome_classe in dir(modulo):
                    if nome_classe != "Plugin" and nome_classe.isupper():
                        classe_plugin = getattr(modulo, nome_classe)
                        if issubclass(classe_plugin, Plugin):
                            plugin = classe_plugin()
                            plugins.append(plugin)
                            logger.debug(f"Plugin {nome_classe} carregado com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao carregar plugin {nome_modulo}: {e}")
    return plugins


def conectar_banco_dados(config):
    """
    Conecta ao banco de dados usando o plugin BancoDados.

    Args:
        config (ConfigParser): Objeto com as configurações do bot.
    """
    try:
        banco_dados = obter_banco_dados()
        banco_dados.inicializar(config)
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise


def armazenar_dados(config, dados, par, timeframe):
    """
    Armazena os dados no banco de dados usando o plugin BancoDados.

    Args:
        config (ConfigParser): Objeto com as configurações do bot.
        dados (list): Lista de dados a serem armazenados.
        par (str): Par de moedas.
        timeframe (str): Timeframe dos dados.
    """
    try:
        banco_dados = obter_banco_dados()
        banco_dados.inserir_dados(
            "klines",
            {
                "par": par,
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

    return Conexao()


def obter_banco_dados():
    """
    Fornece acesso ao plugin de Banco de Dados.

    Returns:
        BancoDados: Instância do plugin de Banco de Dados.
    """
    from plugins.banco_dados import BancoDados

    return BancoDados()


def obter_analise_candles():
    """
    Fornece acesso ao plugin de Análise de Candles.

    Returns:
        AnaliseCandles: Instância do plugin de Análise de Candles.
    """
    from plugins.analise_candles import AnaliseCandles

    return AnaliseCandles()


def obter_armazenamento():
    """
    Fornece acesso ao plugin de Armazenamento.

    Returns:
        Armazenamento: Instância do plugin de Armazenamento.
    """
    from plugins.armazenamento import Armazenamento

    return Armazenamento()


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

    return ExecucaoOrdens()


def obter_medias_moveis():
    """
    Fornece acesso ao plugin de Médias Móveis.

    Returns:
        MediasMoveis: Instância do plugin de Médias Móveis.
    """
    from plugins.medias_moveis import MediasMoveis

    return MediasMoveis()


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

    return IndicadoresOsciladores()


def obter_indicadores_tendencia():
    """
    Fornece acesso ao plugin de Indicadores de Tendência.

    Returns:
        IndicadoresTendencia: Instância do plugin de Indicadores de Tendência.
    """
    from plugins.indicadores.indicadores_tendencia import IndicadoresTendencia

    return IndicadoresTendencia()


def obter_indicadores_volatilidade():
    """
    Fornece acesso ao plugin de Indicadores de Volatilidade.

    Returns:
        IndicadoresVolatilidade: Instância do plugin de Indicadores de Volatilidade.
    """
    from plugins.indicadores.indicadores_volatilidade import IndicadoresVolatilidade

    return IndicadoresVolatilidade()


def obter_indicadores_volume():
    """
    Fornece acesso ao plugin de Indicadores de Volume.

    Returns:
        IndicadoresVolume: Instância do plugin de Indicadores de Volume.
    """
    from plugins.indicadores.indicadores_volume import IndicadoresVolume

    return IndicadoresVolume()


def obter_outros_indicadores():
    """
    Fornece acesso ao plugin de Outros Indicadores.

    Returns:
        OutrosIndicadores: Instância do plugin de Outros Indicadores.
    """
    from plugins.indicadores.outros_indicadores import OutrosIndicadores

    return OutrosIndicadores()
