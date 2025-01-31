import datetime
import os
import time
from dotenv import load_dotenv
import ccxt
from loguru import logger
import plugins
from plugins.banco_dados import BancoDados
from trading_core import Core
from plugins import carregar_plugins
from configparser import ConfigParser


# 1. Configuração do Loguru
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

data_hoje = datetime.datetime.now().strftime("%d%m%Y")

logger.add(
    os.path.join(logs_dir, f"bot{data_hoje}.log"),
    rotation="5 MB",
    retention="10 days",
    level="DEBUG",
    format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {module} | {function} | {line} | {message}",
)

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do bot (carregadas do arquivo config.ini)
config = {}


# Bloco principal do script
if __name__ == "__main__":
    # Carrega as configurações do arquivo config.ini
    def load_config_from_file(filename):
        config = ConfigParser()
        config.read(filename)
        return config

    config = load_config_from_file("config.ini")

    # Cria a instância do Core, passando a configuração carregada
    core = Core(config)

    # Cria uma instância do Banco de Dados
    banco_dados = BancoDados(None)

    # Injeta a instância do Banco de Dados no Core
    core.plugin_banco_dados = banco_dados

    # Conecta ao banco de dados
    core.conectar_banco_dados()

    # Carrega os plugins
    plugins = carregar_plugins()

    # Inicializa os plugins
    for plugin in plugins:
        try:
            core.inject(plugin.inicializar)
        except Exception as e:
            logger.exception(
                f"Erro ao inicializar o plugin {plugin.__class__.__name__}: {e}"
            )
            exit(1)

    # Inicializa os plugins de indicadores (assumindo que existe um método `inicializar_indicadores` no Core)
    core.inject(core.inicializar_indicadores)

    # Loop principal do bot
    while True:
        try:
            exchange = core.obter_exchange()

            markets = exchange.load_markets()
            pares_usdt = [par for par in markets.keys() if par.endswith("USDT")]

            logger.info("Iniciando coleta de dados...")

            for par in pares_usdt:
                for timeframe in config["timeframes"]:
                    try:
                        klines = exchange.fetch_ohlcv(par, timeframe)
                        dados = []
                        for kline in klines:
                            dados.append(
                                {
                                    "timestamp": kline[0],
                                    "open": kline[1],
                                    "high": kline[2],
                                    "low": kline[3],
                                    "close": kline[4],
                                    "volume": kline[5],
                                }
                            )

                        if not dados:
                            logger.warning(
                                f"Dados vazios para {par} - {timeframe}. Pulando análise."
                            )
                            continue  # Pula para o próximo par/timeframe

                        # Armazena os dados (assumindo que existe um método `armazenar_dados` no Core)
                        core.armazenar_dados(dados, par, timeframe)

                        for plugin in plugins:
                            try:
                                plugin.executar(dados, par, timeframe)
                            except Exception as e:
                                logger.error(
                                    f"Erro ao executar plugin {plugin.__class__.__name__} para {par} - {timeframe}: {e}"
                                )

                    except Exception as e:
                        logger.error(
                            f"Erro ao coletar dados ou analisar {par} - {timeframe}: {e}"
                        )

            logger.debug(f"Aguardando {30} segundos para a próxima coleta...")
            time.sleep(30)

        except ccxt.ExchangeError as e:
            logger.error(f"Erro na exchange: {e}")
            time.sleep(60)
        except Exception as e:
            logger.exception(f"Erro inesperado: {e}")

        # Finaliza os plugins
        for plugin in plugins:
            plugin.finalizar()
