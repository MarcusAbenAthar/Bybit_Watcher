from loguru import logger

import psycopg2
from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_banco_dados


class Armazenamento(Plugin):
    """
    Plugin para armazenar os dados dos candles no banco de dados.
    """

    def __init__(self):
        super().__init__()

    def executar(self, dados, symbol, timeframe, config):
        """
        Insere os dados das velas no banco de dados.
        """
        try:
            # Obtém o banco de dados quando necessário
            banco_dados = obter_banco_dados(config)

            # Usa a conexão com o banco de dados
            banco_dados.inserir_dados_klines(dados)

            logger.debug(
                f"Dados de {symbol} - {timeframe} inseridos no banco de dados."
            )

        except Exception as error:
            logger.error(f"Erro ao inserir dados no PostgreSQL: {error}")
