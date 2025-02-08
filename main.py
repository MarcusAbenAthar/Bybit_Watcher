# main.py

"""
Módulo principal do bot de trading.
"""

import os
import time
import sys
import signal
import logging
import logging.config
from configparser import ConfigParser
from dotenv import load_dotenv
from logging_config import LOGGING_CONFIG
from sinais_logging import SINAIS_LOGGING_CONFIG
from plugins.gerenciador_banco import gerenciador_banco
from plugins.validador_dados import ValidadorDados
from plugins.gerente_plugin import (
    gerente_plugin,
    obter_conexao,
    obter_banco_dados,
    inicializar_banco_dados,
)
from plugins.gerenciador_bot import GerenciadorBot

# Configuração do logger
logging.config.dictConfig(LOGGING_CONFIG)
logging.config.dictConfig(SINAIS_LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Configurações iniciais
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Carrega variáveis de ambiente
load_dotenv()


def load_config_from_file(filename):
    """Carrega configurações do arquivo."""
    try:
        config = ConfigParser()
        config.read(filename)
        return config
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {e}")
        raise


def signal_handler(signum, frame):
    """Handler para encerramento gracioso."""
    try:
        logger.info("Recebido sinal de interrupção...")
        gerenciador_banco.fechar_conexao()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro ao encerrar bot: {e}")
        sys.exit(1)


def processar_par(symbol, timeframe, validador, exchange):
    """
    Processa um par específico.

    Args:
        symbol (str): Símbolo do par
        timeframe (str): Timeframe para análise
        validador (ValidadorDados): Instância do validador
        exchange (Exchange): Instância da exchange

    Returns:
        list: Lista de candles válidos ou None
    """
    try:
        logger.debug(f"Processando {symbol} - {timeframe}")

        dados = exchange.fetch_ohlcv(symbol, timeframe)

        if not validador.validar_dados_completos(dados, symbol, timeframe):
            return None

        logger.debug(f"Dados válidos obtidos para {symbol}")
        return dados

    except Exception as e:
        logger.error(f"Erro ao processar {symbol}-{timeframe}: {e}")
        return None


def main():
    """Função principal do bot."""
    try:
        logger.info("Iniciando bot...")

        # Inicializações
        config = load_config_from_file("config.ini")
        gerenciador = GerenciadorBot(config)

        # Carrega plugins e conexões
        plugins = gerente_plugin.carregar_plugins("plugins", config)
        conexao_bybit = obter_conexao()
        conexao_bybit.inicializar(config)

        logger.info("Bot iniciado com sucesso")

        # Loop principal
        while True:
            try:
                mercados = conexao_bybit.carregar_mercados()
                for symbol, dados in mercados.items():
                    if gerenciador.validar_mercado(dados):
                        for timeframe in gerenciador.timeframes:
                            dados = gerenciador.processar_par(
                                symbol, timeframe, conexao_bybit.exchange
                            )
                            if dados:
                                gerenciador.processar_plugins(
                                    plugins, dados, symbol, timeframe
                                )

                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("Interrupção do teclado detectada")
                gerenciador_banco.fechar_conexao()
                sys.exit(0)

    except Exception as e:
        logger.exception(f"Erro fatal no bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
