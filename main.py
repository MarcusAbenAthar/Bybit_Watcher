import datetime
import os
import time
from dotenv import load_dotenv
from loguru import logger
import ccxt
from plugins import carregar_plugins
from plugins.conexao import Conexao

# 1. Configuração do Loguru
logs_dir = "logs"  # Diretório para armazenar os logs
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Obtém a data de hoje no formato DD-MM-YYYY
data_hoje = datetime.datetime.now().strftime("%d%m%Y")

logger.add(
    os.path.join(logs_dir, f"bot{data_hoje}.log"),
    rotation="5 MB",  # Rotação de arquivos a cada 5 MB
    retention="10 days",  # Mantém os logs por 10 dias
    level="DEBUG",  # Nível de log
    format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {module} | {function} | {line} | {message}",  # Formato do log
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

# Carrega os plugins
plugins = carregar_plugins("plugins", config)

# Inicializa os plugins
for plugin in plugins:
    try:
        plugin.inicializar()
    except Exception as e:
        logger.exception(
            f"Erro ao inicializar o plugin {plugin.__class__.__name__}: {e}"
        )
        exit(1)

# Obtém o plugin de conexão
plugin_conexao = next((p for p in plugins if isinstance(p, Conexao)), None)
if plugin_conexao is None:
    logger.error("Plugin de conexão não encontrado!")
    exit(1)
# Loop principal do bot
while True:  # Remove a verificação do plugin de interrupção
    try:
        # Obtém o objeto exchange do plugin de conexão
        exchange = plugin_conexao.obter_exchange()

        # Carrega todos os mercados da Bybit
        markets = exchange.load_markets()

        # Filtra apenas os pares USDT
        pares_usdt = [par for par in markets.keys() if par.endswith("USDT")]

        # 2. Coleta de dados de mercado
        logger.info("Iniciando coleta de dados...")

        # Coleta os dados de mercado para cada par e timeframe
        for par in pares_usdt:
            for timeframe in config[
                "timeframes"
            ]:  # Remove a verificação do plugin de interrupção
                print(f"Coletando dados para {par} - {timeframe}...")
                logger.debug(f"Coletando dados para {par} - {timeframe}...")
                klines = exchange.fetch_ohlcv(par, timeframe)

                # Executa os plugins com os dados coletados
                for plugin in plugins:
                    if (
                        plugin != plugin_conexao
                    ):  # Remove a verificação do plugin de interrupção
                        print(
                            f"Executando plugin {plugin.__class__.__name__} para {par} - {timeframe}..."
                        )
                        logger.debug(
                            f"Executando plugin {plugin.__class__.__name__} para {par} - {timeframe}..."
                        )
                        plugin.executar(klines, par, timeframe)

        # Aguarda um intervalo de tempo antes da próxima iteração
        print(f"Aguardando {30} segundos para a próxima coleta...")
        logger.debug(f"Aguardando {30} segundos para a próxima coleta...")
        time.sleep(30)

    except ccxt.NetworkError as e:
        print(f"Erro de rede: {e}")
        logger.error(f"Erro de rede: {e}")
        time.sleep(60)
    except ccxt.ExchangeError as e:
        print(f"Erro na exchange: {e}")
        logger.error(f"Erro na exchange: {e}")
        time.sleep(60)
    except Exception as e:
        # Captura outras interrupções inesperadas
        logger.exception(f"Erro inesperado: {e}")

    # Finaliza os plugins
    for plugin in plugins:
        plugin.finalizar()
