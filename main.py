"""
Módulo principal do bot de trading.

Este módulo é responsável por iniciar o bot, carregar as configurações,
conectar ao banco de dados, carregar os plugins e executar o loop principal.
"""

import datetime
import os
import time
from dotenv import load_dotenv
import ccxt
from loguru import logger
from plugins.gerente_plugin import (
    carregar_plugins,
    conectar_banco_dados,
    armazenar_dados,
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

# Carrega as variáveis de ambiente
load_dotenv()

# Bloco principal do script
if __name__ == "__main__":
    # Carrega as configurações do arquivo config.ini
    def load_config_from_file(filename):
        config = ConfigParser()
        config.read(filename)
        return config

    config = load_config_from_file("config.ini")

    # Conecta ao banco de dados
    conectar_banco_dados(
        config
    )  # Passa as configurações para a função conectar_banco_dados

    # Carrega os plugins
    plugins = carregar_plugins("plugins")

    # Loop principal do bot
    while True:
        try:
            exchange = ccxt.bybit(
                {  # Inicializa a exchange bybit aqui
                    "apiKey": config.get("Bybit", "API_KEY"),
                    "secret": config.get("Bybit", "API_SECRET"),
                    "enableRateLimit": True,
                }
            )
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
                                    "timestamp": kline,  # Corrigido o acesso aos dados do kline
                                    "open": kline,
                                    "high": kline,
                                    "low": kline,
                                    "close": kline,
                                    "volume": kline,
                                }
                            )

                        if not dados:
                            logger.warning(
                                f"Dados vazios para {par} - {timeframe}. Pulando análise."
                            )
                            continue

                        # Armazena os dados
                        armazenar_dados(
                            config, dados, par, timeframe
                        )  # Passa as configurações para a função armazenar_dados

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
