from venv import logger  # Certifique-se de ter o logger configurado corretamente
from trading_core import Core
import ccxt
from plugins.plugin import Plugin


class Conexao(Plugin):
    """
    Plugin para gerenciar a conexão com a exchange, agora integrado com o Core.
    """

    def __init__(self, core: Core):  # Agora recebe o Core na inicialização
        self.core = core
        super().__init__(
            self.core.config
        )  # Inicializa a classe Plugin com as configurações do Core

    def inicializar(self):
        """
        Estabelece a conexão com a Bybit usando o CCXT, utilizando configurações do Core.
        """
        try:
            logger.info("Inicializando a conexão com a Bybit...")
            self.exchange = ccxt.bybit(
                {
                    "apiKey": self.config.get(
                        "Bybit", "API_KEY"
                    ),  # Obtém as credenciais do Core
                    "secret": self.config.get("Bybit", "API_SECRET"),
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
        Fecha a conexão com a Bybit, se ela foi estabelecida.
        """
        try:
            if self.exchange:
                logger.info("Fechando a conexão com a Bybit...")
                self.exchange.close()
                logger.info("Conexão com a Bybit fechada com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao fechar a conexão com a Bybit: {e}")
