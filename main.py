# main.py

"""
Módulo principal do bot de trading.

Este módulo é responsável por iniciar o bot, carregar as configurações,
conectar ao banco de dados, carregar os plugins e executar o loop principal.
"""

import datetime
import os
import time
import ccxt
from dotenv import load_dotenv
from loguru import logger
from plugins.gerente_plugin import (
    carregar_plugins,
    obter_conexao,
    obter_banco_dados,
    inicializar_banco_dados,
)
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

# Define os timeframes diretamente
timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

# Carrega as variáveis de ambiente
load_dotenv()

# Inicializa um conjunto vazio
pares_processados = set()


# Carrega as configurações do arquivo config.ini
def load_config_from_file(filename):
    config = ConfigParser()
    config.read(filename)
    return config


# Bloco principal do script
if __name__ == "__main__":
    config = load_config_from_file("config.ini")

    # Carrega os plugins
    plugins = carregar_plugins("plugins")

    # Obtém a instância do plugin Conexao
    conexao_bybit = obter_conexao()

    # Inicializa o plugin Conexao
    conexao_bybit.inicializar(config)

    # Inicializa o banco de dados (fora do loop)
    inicializar_banco_dados(config)

    # Obtém a exchange do plugin Conexao
    exchange = conexao_bybit.exchange

    banco_dados = obter_banco_dados(config)

    # Carrega os mercados
    conexao_bybit.carregar_mercados()

    # Obtém os pares de moedas USDT
    pares_usdt = conexao_bybit.pares_usdt
    logger.info(f"Pares USDT: {pares_usdt}")

# Loop principal do bot
while True:
    try:
        logger.info("Iniciando coleta de dados...")
        for symbol in pares_usdt:
            if symbol not in pares_processados:
                logger.info(f"Coletando dados para o symbol {symbol}...")
                pares_processados.add(symbol)
            for timeframe in timeframes:
                try:
                    # Coleta os dados
                    klines = exchange.fetch_ohlcv(
                        symbol,
                        timeframe,
                        params={"category": "linear"},
                    )
                    # Formata os dados como uma lista de tuplas
                    dados = [
                        (
                            symbol,
                            timeframe,
                            kline,
                            kline,
                            kline,
                            kline,
                            kline,
                            kline,
                        )
                        for kline in klines
                    ]

                    if not dados:
                        logger.warning(
                            f"Dados vazios para {symbol} - {timeframe}. Pulando análise."
                        )
                        continue

                    # Armazena os dados no banco de dados
                    banco_dados.inserir_dados_klines(dados)

                    # Executa os plugins
                    for plugin in plugins:
                        try:
                            plugin.executar(dados, symbol, timeframe, config)
                        except Exception as e:
                            logger.error(
                                f"Erro ao executar plugin {plugin.__class__.__name__} "
                                f"para {symbol} - {timeframe}: {e}"
                            )

                except Exception as e:
                    logger.error(
                        f"Erro ao coletar dados ou analisar {symbol} - {timeframe}: {e}"
                    )

        logger.debug(f"Aguardando {30} segundos para a próxima coleta...")
        time.sleep(30)

    except ccxt.ExchangeError as e:
        logger.error(f"Erro na exchange: {e}")
        time.sleep(60)
    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
