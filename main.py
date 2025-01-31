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

# Configurações do bot
config = {
    "api_key": os.getenv("BYBIT_API_KEY"),
    "api_secret": os.getenv("BYBIT_API_SECRET"),
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "timeframes": ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
}

# Bloco principal do script
if __name__ == "__main__":
    # Carrega as configurações
    def load_config_from_file(filename):
        config = ConfigParser()
        config.read(filename)
        return config

    config = load_config_from_file("config.ini")

    # Cria uma instância do Banco de Dados
    banco_dados = BancoDados(None)

    # Cria a instância do Core, passando a instância do Banco de Dados
    core = Core(config, banco_dados)  # Passa as configurações para o Core

    # Conecta ao banco de dados
    core.conectar_banco_dados()
    # Inicializa os plugins
    for plugin in plugins:
        try:
            core.inject(plugin.inicializar)
        except Exception as e:
            logger.exception(
                f"Erro ao inicializar o plugin {plugin.__class__.__name__}: {e}"
            )
            exit(1)

    # Inicializa os plugins de indicadores
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

        except ccxt.NetworkError as e:
            logger.error(f"Erro de rede: {e}")
            time.sleep(60)
        except ccxt.ExchangeError as e:
            logger.error(f"Erro na exchange: {e}")
            time.sleep(60)
        except Exception as e:
            logger.exception(f"Erro inesperado: {e}")

        # Finaliza os plugins
        for plugin in plugins:
            plugin.finalizar()
