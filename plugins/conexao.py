from venv import logger
from core import Core
import ccxt
from plugins.plugin import Plugin


class Conexao(Plugin):
    """
    Plugin para gerenciar a conexão com a exchange.
    """

    def __init__(self, container: AppModule):
        self.container = container
        super().__init__(container.config())

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
