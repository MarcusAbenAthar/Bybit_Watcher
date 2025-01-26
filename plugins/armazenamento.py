import psycopg2
from loguru import logger
from plugins.banco_dados import BancoDados
from .plugin import Plugin


class Armazenamento(Plugin):
    """
    Plugin para armazenar os dados das velas (klines) no banco de dados.
    """

    def __init__(self, config):
        super().__init__(config)
        self.banco_dados = None  # Referência ao plugin BancoDados

    def inicializar(self, plugins):
        """
        Obtém a referência ao plugin BancoDados.
        """
        # Procura o plugin BancoDados na lista de plugins
        for plugin in plugins:
            if isinstance(plugin, BancoDados):
                self.banco_dados = plugin
                # Remove a linha abaixo:
                # self.banco_dados.inicializar(plugins)
                break
        if not self.banco_dados:
            logger.error("Plugin BancoDados não encontrado!")
            raise Exception("Plugin BancoDados não encontrado!")

    def executar(self, dados, par, timeframe):
        """
        Insere os dados das velas no banco de dados.

        Args:
            dados (list): Lista de klines.
            par (str): Par de criptomoedas.
            timeframe (str): Timeframe dos dados.
        """
        try:
            conn = self.banco_dados.conn
            cursor = conn.cursor()

            for kline in dados:
                timestamp = int(kline[0] / 1000)  # Converte o timestamp para segundos
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
        except psycopg2.OperationalError as e:
            logger.error(f"Erro de conexão com o banco de dados: {e}")
            self.banco_dados.inicializar(plugins)
