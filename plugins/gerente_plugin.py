# plugins/gerente_plugin.py

"""
Gerenciador de plugins para o bot de trading.

Este módulo é responsável por carregar e fornecer acesso aos plugins do bot,
seguindo as Regras de Ouro para garantir a clareza, modularidade e 
testabilidade do código.

"""

from plugins.plugin import Plugin
import logging
import os
import importlib

logger = logging.getLogger(__name__)


class GerentePlugin(Plugin):
    """
    Gerenciador central de plugins do sistema.
    """

    _instance = None  # Singleton instance
    _singleton_plugins = {
        "BancoDados": None,
        "ValidadorDados": None,
        "GerentePlugin": None,
        "Conexao": None,
        "GerenciadorBanco": None,
    }
    _config = None

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(GerentePlugin, cls).__new__(cls)
            cls._config = config
        return cls._instance

    def __init__(self, config=None):  # <-- Added config parameter
        if not hasattr(self, "initialized"):
            super().__init__()
            self.nome = "Gerente de Plugins"
            self.descricao = "Gerencia todos os plugins do sistema"
            self.plugins = []
            self._config = config  # <-- Store config
            self.initialized = True

    def carregar_plugins(self, diretorio, config=None):
        """Carrega todos os plugins de um determinado diretório."""
        try:
            # Lista de plugins na ordem de carregamento
            plugins_ordem = [
                # Core plugins
                "conexao",
                "banco_dados",
                "validador_dados",
                # Análise plugins
                "calculo_alavancagem",
                "analise_candles",
                "medias_moveis",
                "price_action",
                # Trading plugins
                "calculo_risco",
                "execucao_ordens",
                "sinais_plugin",
                # Indicadores plugins
                "indicadores/indicadores_osciladores",
                "indicadores/indicadores_tendencia",
                "indicadores/indicadores_volatilidade",
                "indicadores/indicadores_volume",
                "indicadores/outros_indicadores",
                # Gerenciamento
                "gerenciador_bot",
            ]

            # Carregar cada plugin na ordem definida
            for plugin_nome in plugins_ordem:
                caminho = os.path.join(diretorio, f"{plugin_nome}.py")

                try:
                    if os.path.exists(caminho):
                        # Carrega o módulo
                        spec = importlib.util.spec_from_file_location(
                            plugin_nome, caminho
                        )
                        modulo = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(modulo)

                        # Instancia o plugin
                        plugin = self._carregar_plugin(plugin_nome, config)

                        if plugin:
                            self.plugins.append(plugin)
                            logger.info(
                                f"Plugin carregado: {plugin.__class__.__name__} ({plugin_nome})"
                            )

                except Exception as e:
                    logger.error(f"Erro ao carregar plugin {plugin_nome}: {str(e)}")
                    continue

            # Inicializa plugins
            for plugin in self.plugins:
                if hasattr(plugin, "inicializar"):
                    plugin.inicializar()

            logger.info(f"=== Total de plugins carregados: {len(self.plugins)} ===")
            return True

        except Exception as erro:
            logger.error(f"Erro no carregamento de plugins: {str(erro)}")
            return False

    def _carregar_plugin(self, nome_modulo, config=None):
        """Carrega um plugin específico."""
        try:
            modulo = importlib.import_module(f"plugins.{nome_modulo}")

            for nome_attr in dir(modulo):
                attr = getattr(modulo, nome_attr)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr != Plugin
                ):

                    # Configuração específica para plugins que precisam de config
                    if attr.__name__ in ["BancoDados", "GerenciadorBanco"]:
                        plugin = attr(config)
                    else:
                        plugin = attr()

                    # Verifica singleton
                    if attr.__name__ in self._singleton_plugins:
                        if self._singleton_plugins[attr.__name__] is not None:
                            return None
                        self._singleton_plugins[attr.__name__] = plugin

                    return plugin

            return None

        except Exception as e:
            logger.error(f"Erro ao carregar módulo {nome_modulo}: {str(e)}")
            return None

    def _verificar_plugin(self, plugin):
        """Verifica se um plugin está funcionando corretamente."""
        try:
            if hasattr(plugin, "verificar_inicializacao"):
                plugin.verificar_inicializacao()
            if hasattr(plugin, "validar"):
                plugin.validar()
            return True
        except Exception as e:
            logger.error(f"Falha na verificação do plugin {plugin.nome}: {e}")
            return False

    def interromper_execucao(self):
        """Gerencia a interrupção segura do bot."""
        try:
            logger.info("Iniciando encerramento seguro do bot...")

            # Fecha conexão com banco se estiver aberta
            if hasattr(self, "_db") and self._db is not None:
                try:
                    self._db.fechar_conexao()
                    logger.info("Conexão com banco de dados encerrada")
                except Exception as e:
                    logger.error(f"Erro ao fechar conexão com banco: {e}")

            logger.info("Bot encerrado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao encerrar bot: {e}")
            return False

    def executar_ciclo(self):
        """Executa um ciclo completo do bot."""
        try:
            # Obtém conexão
            conexao = self._singleton_plugins.get("Conexao")
            if not conexao:
                raise ValueError("Conexão não inicializada")

            # Obtém configurações
            timeframe = self._config.get("timeframe", "1h")
            symbols = self._config.get("symbols", ["BTCUSDT"])

            # Executa para cada símbolo
            for symbol in symbols:
                try:
                    dados = conexao.obter_dados_mercado(symbol, timeframe)

                    # Executa plugins
                    for plugin in self.plugins:
                        if hasattr(plugin, "executar"):
                            try:
                                plugin.executar(dados, symbol, timeframe)
                            except Exception as e:
                                logger.error(
                                    f"Erro ao executar plugin {plugin.nome}: {str(e)}"
                                )

                except Exception as e:
                    logger.error(f"Erro ao processar símbolo {symbol}: {str(e)}")
                    continue

            return True

        except Exception as erro:
            logger.error(f"Erro no ciclo de execução: {str(erro)}")
            return False


# Instância global do gerente
gerente_plugin = GerentePlugin()


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
