from venv import logger

import psycopg2
from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_banco_dados


class Armazenamento(Plugin):
    """
    Plugin para armazenar os dados dos candles no banco de dados.
    """

    def __init__(self):
        super().__init__()

    def inicializar(self, config):
        pass

    def executar(self, dados, par, timeframe):
        """
        Insere os dados das velas no banco de dados.
        """
        try:
            # Usa a conexão com o banco de dados fornecida pelo Core
            conn = obter_banco_dados().conn  # Obtém a conexão do banco de dados
            cursor = conn.cursor()

            for kline in dados:
                timestamp = int(kline / 1000)
                open = kline
                high = kline
                low = kline
                close = kline
                volume = kline

                try:
                    cursor.execute(
                        """
                        INSERT INTO klines (par, timeframe, timestamp, open, high, low, close, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (par, timeframe, timestamp) DO NOTHING;  -- Evita duplicatas
                        """,
                        (par, timeframe, timestamp, open, high, low, close, volume),
                    )
                except Exception as e:
                    logger.error(f"Erro ao inserir kline: {e}")
                    conn.rollback()  # Faz o rollback da transação em caso de erro

            conn.commit()
            logger.debug(f"Dados de {par} - {timeframe} inseridos no banco de dados.")

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados no PostgreSQL: {error}")
