from venv import logger

import psycopg2
from plugins.plugin import Plugin


class Armazenamento(Plugin):
    """
    Plugin para armazenar os dados dos candles no banco de dados.
    """

    def __init__(self, core):  # Recebe o Core como argumento
        self.core = core
        self.config = core.config  # Acessa as configurações através do Core
        # self.banco_dados = core.banco_dados # Acesso direto não é mais necessário aqui

    def inicializar(self, plugins):
        pass

    def executar(self, dados, par, timeframe):
        """
        Insere os dados das velas no banco de dados.
        """
        try:
            # Usa a conexão com o banco de dados fornecida pelo Core
            conn = self.core.banco_dados.conexao
            cursor = conn.cursor()

            for kline in dados:
                timestamp = int(kline[0] / 1000)
                open = kline[1]
                high = kline[2]
                low = kline[3]
                close = kline[4]
                volume = kline[5]

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
