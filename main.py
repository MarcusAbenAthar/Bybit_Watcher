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

    # Carrega os plugins passando o config
    plugins = carregar_plugins("plugins", config)

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
    mercados = conexao_bybit.carregar_mercados()

# Loop principal do bot
while True:
    try:
        logger.info("Iniciando coleta de dados...")
        for symbol, dados in mercados.items():
            if (
                dados.get("type") == "swap"
                and dados.get("settle") == "USDT"
                and dados.get("linear")
                and not dados.get("id", "").endswith("/USDT:USDT")
            ):
                # Limpa o nome do símbolo mantendo o USDT no final
                symbol_limpo = symbol.replace("/USDT:USDT", "USDT")

                if symbol_limpo not in pares_processados:
                    logger.info(f"Coletando dados para o symbol {symbol_limpo}...")
                    pares_processados.add(symbol_limpo)

                for timeframe in timeframes:
                    try:
                        # Adiciona um pequeno delay entre as chamadas
                        time.sleep(0.5)

                        # Coleta os dados usando o símbolo original para a API
                        klines = exchange.fetch_ohlcv(
                            symbol,
                            timeframe,
                            params={"category": "linear"},
                            limit=200,
                        )

                        if not klines:
                            logger.warning(
                                f"Sem dados disponíveis para {symbol_limpo} - {timeframe}"
                            )
                            continue

                        # Formata os dados usando o símbolo limpo
                        dados = [
                            (
                                symbol_limpo,
                                timeframe,
                                kline[0],
                                kline[1],
                                kline[2],
                                kline[3],
                                kline[4],
                                kline[5],
                            )
                            for kline in klines
                        ]

                        # Armazena os dados no banco de dados com o símbolo limpo
                        banco_dados.inserir_dados_klines(dados)

                        # Processa os dados através dos plugins na ordem correta
                        resultados = {}

                        # Primeiro processa indicadores
                        for plugin in plugins:
                            if plugin.nome in [
                                "Indicadores de Tendência",
                                "Médias Móveis",
                            ]:
                                resultado = plugin.executar(
                                    dados, symbol_limpo, timeframe
                                )
                                if resultado:
                                    chave = (
                                        plugin.nome.lower()
                                        .replace(" ", "_")
                                        .replace("ê", "e")
                                    )
                                    resultados[chave] = resultado

                        # Depois processa sinais
                        for plugin in plugins:
                            if plugin.nome == "Sinais" and resultados:
                                plugin.executar(resultados, symbol_limpo, timeframe)

                        # Por fim, processa outros plugins
                        for plugin in plugins:
                            if plugin.nome not in [
                                "Indicadores de Tendência",
                                "Médias Móveis",
                                "Sinais",
                            ]:
                                try:
                                    plugin.executar(dados, symbol_limpo, timeframe)
                                except Exception as e:
                                    logger.error(
                                        f"Erro ao executar plugin {plugin.__class__.__name__} "
                                        f"para {symbol_limpo} - {timeframe}: {e}"
                                    )

                    except ccxt.RateLimitExceeded:
                        logger.warning(
                            f"Rate limit atingido para {symbol_limpo}. Aguardando..."
                        )
                        time.sleep(5)
                        continue

                    except ccxt.ExchangeError as e:
                        logger.error(
                            f"Erro da exchange para {symbol_limpo} - {timeframe}: {e}"
                        )
                        continue

                    except Exception as e:
                        logger.error(
                            f"Erro ao coletar dados ou analisar {symbol_limpo} - {timeframe}: {e}"
                        )
                        continue

        logger.debug(f"Aguardando {30} segundos para a próxima coleta...")
        time.sleep(30)

    except ccxt.ExchangeError as e:
        logger.error(f"Erro na exchange: {e}")
        time.sleep(60)
    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
        time.sleep(30)
