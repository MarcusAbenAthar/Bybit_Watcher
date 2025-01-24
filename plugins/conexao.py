# plugins/conexao.py

import ccxt
from loguru import logger  # Importa o logger do Loguru

from .plugin import Plugin


class Conexao(Plugin):
    """
    Plugin responsável por estabelecer e gerenciar a conexão com a Bybit.
    """

    def __init__(self, config):
        """
        Inicializa o plugin de conexão.

        Args:
          config: Um dicionário com as configurações do bot.
        """
        super().__init__(config)
        self.exchange = None

    def inicializar(self):
        """
        Estabelece a conexão com a Bybit usando o CCXT.
        """
        try:
            logger.info("Inicializando a conexão com a Bybit...")
            self.exchange = ccxt.bybit(
                {
                    "apiKey": self.config["api_key"],
                    "secret": self.config["api_secret"],
                    "enableRateLimit": True,
                }
            )
            logger.info("Conexão com a Bybit estabelecida com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao conectar na Bybit: {e}")
            raise  # Lança a exceção para tratamento no main.py

    def obter_exchange(self):
        """
        Retorna o objeto exchange do CCXT.

        Returns:
          O objeto exchange do CCXT.
        """
        return self.exchange

    def finalizar(self):
        """
        Fecha a conexão com a Bybit.
        """
        try:
            if self.exchange:
                logger.info("Fechando a conexão com a Bybit...")
                self.exchange.close()
                logger.info("Conexão com a Bybit fechada com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao fechar a conexão com a Bybit: {e}")
