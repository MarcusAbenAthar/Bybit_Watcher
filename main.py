import datetime
import os
import time
from dotenv import load_dotenv
import ccxt
from loguru import logger
from core import Core  # Importa o Core
from plugins import carregar_plugins

# Remova as importações diretas dos plugins de indicadores
# Eles serão inicializados e acessados através do Core

# 1. Configuração do Loguru (sem alterações)
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

# Carrega as variáveis de ambiente (sem alterações)
load_dotenv()

# Configurações do bot (sem alterações)
config = {
    "api_key": os.getenv("BYBIT_API_KEY"),
    "api_secret": os.getenv("BYBIT_API_SECRET"),
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "timeframes": ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"],
}

# Cria o Core
core = Core()
core.carregar_configuracoes_dict(config)  # Carrega as configurações no Core

# Carrega os plugins, injetando o Core
plugins = carregar_plugins("plugins", core)

# Inicializa os plugins, usando o Core para injeção
for plugin in plugins:
    try:
        core.inject(plugin.inicializar)  # Injeção através do Core
    except Exception as e:
        logger.exception(
            f"Erro ao inicializar o plugin {plugin.__class__.__name__}: {e}"
        )
        exit(1)

# Inicializa os plugins de indicadores (agora através do Core)
core.inject(
    core.inicializar_indicadores
)  # Método no Core para inicializar todos os indicadores

# Loop principal do bot (sem alterações na estrutura geral)
while True:
    try:
        exchange = core.obter_exchange()  # Obtém o exchange do Core

        markets = exchange.load_markets()
        pares_usdt = [par for par in markets.keys() if par.endswith("USDT")]

        logger.info("Iniciando coleta de dados...")

        for par in pares_usdt:
            for timeframe in config["timeframes"]:
                klines = exchange.fetch_ohlcv(par, timeframe)

                core.armazenar_dados(
                    klines, par, timeframe
                )  # Armazenamento através do Core

                for plugin in plugins:
                    if (
                        plugin != core.plugin_conexao
                        and plugin != core.plugin_armazenamento
                    ):  # Acesso aos plugins através do Core
                        plugin.executar(klines, par, timeframe)

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

    # Finaliza os plugins (sem alterações)
    for plugin in plugins:
        plugin.finalizar()
