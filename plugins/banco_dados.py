import psycopg2
from loguru import logger
from .plugin import Plugin


class BancoDados(Plugin):
    """
    Plugin para gerenciar o banco de dados PostgreSQL.
    """

    def __init__(self, config):
        super().__init__(config)
        self.conn = None
        self.cursor = None

    def inicializar(self):
        """
        Conecta ao banco de dados e cria a tabela `klines` se ela não existir.
        """
        try:
            logger.info("Conectando ao banco de dados PostgreSQL...")
            self.conn = psycopg2.connect(
                host="seu_host",
                database="seu_banco_de_dados",
                user="seu_usuario",
                password="sua_senha",
            )
            self.cursor = self.conn.cursor()

            logger.info("Criando a tabela `klines`...")
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS klines (
                    id SERIAL PRIMARY KEY,
                    par TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL
                );
            """
            )
            self.conn.commit()
            logger.info("Tabela `klines` criada com sucesso!")

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao conectar ao PostgreSQL: {error}")
            raise  # Lança a exceção para tratamento no main.py

    def finalizar(self):
        """
        Fecha a conexão com o banco de dados.
        """
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logger.info("Conexão com o PostgreSQL fechada.")
