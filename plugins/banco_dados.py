import configparser
from venv import logger

import psycopg2
from core import Core
from plugins.plugin import Plugin


class BancoDados(Plugin):
    """
    Plugin para gerenciar o banco de dados PostgreSQL.
    """

    def __init__(self, container: AppModule):
        self.container = container
        super().__init__(container.config())

    def criar_tabela(self, nome_tabela, schema="public"):
        """
        Cria uma tabela no banco de dados, caso ela não exista.

        Args:
            nome_tabela (str): Nome da tabela a ser criada.
            schema (str): Nome do schema onde a tabela será criada (padrão: "public").
        """
        try:
            # Verifica se a tabela já existe
            logger.info(
                f"Verificando se a tabela '{schema}.{nome_tabela}' já existe..."
            )
            self.cursor.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}'
                    AND table_name = '{nome_tabela}'
                );
                """
            )
            tabela_existe = self.cursor.fetchone()[0]

            if not tabela_existe:
                # Cria a tabela
                logger.info(f"Criando a tabela '{schema}.{nome_tabela}'...")
                if nome_tabela == "klines":
                    self.cursor.execute(
                        f"""
                        CREATE TABLE {schema}.{nome_tabela} (
                            id SERIAL PRIMARY KEY,
                            par TEXT NOT NULL,
                            timeframe TEXT NOT NULL,
                            timestamp BIGINT NOT NULL,
                            open REAL NOT NULL,
                            high REAL NOT NULL,
                            low REAL NOT NULL,
                            close REAL NOT NULL,
                            volume REAL NOT NULL,
                            UNIQUE (par, timeframe, timestamp)
                        );
                        """
                    )
                elif nome_tabela == "analise_candles":
                    self.cursor.execute(
                        f"""
                        CREATE TABLE {schema}.{nome_tabela} (
                            id SERIAL PRIMARY KEY,
                            par TEXT NOT NULL,
                            timeframe TEXT NOT NULL,
                            timestamp BIGINT NOT NULL,
                            padrao TEXT,
                            classificacao TEXT,
                            sinal TEXT,
                            stop_loss REAL,
                            take_profit REAL,
                            UNIQUE (par, timeframe, timestamp)
                        );
                        """
                    )
                elif nome_tabela == "medias_moveis":
                    self.cursor.execute(
                        f"""
                        CREATE TABLE {schema}.{nome_tabela} (
                            id SERIAL PRIMARY KEY,
                            par TEXT NOT NULL,
                            timeframe TEXT NOT NULL,
                            timestamp BIGINT NOT NULL,
                            sinal TEXT,
                            stop_loss REAL,
                            take_profit REAL,
                            UNIQUE (par, timeframe, timestamp)
                        );
                        """
                    )
                # ... (adicionar código para criar outras tabelas) ...

                self.conn.commit()
                logger.info(f"Tabela '{schema}.{nome_tabela}' criada com sucesso!")
            else:
                logger.info(f"Tabela '{schema}.{nome_tabela}' já existe.")

        except psycopg2.OperationalError as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
            raise

        except psycopg2.ProgrammingError as e:
            logger.error(f"Erro na consulta SQL: {e}")
            raise

        except Exception as e:
            logger.error(f"Erro genérico: {e}")
            raise

    def inicializar(self, plugins):
        """
        Conecta ao banco de dados e cria as tabelas necessárias.
        """
        try:
            self.plugins = plugins  # Armazene a lista de plugins
            logger.info("Conectando ao banco de dados PostgreSQL...")
            config = configparser.ConfigParser()
            config.read("config.ini")
            db_config = config["database"]

            self.conn = psycopg2.connect(
                host=db_config["host"],
                database=db_config["database"],
                user=db_config["user"],
                password=db_config["password"],
                client_encoding="UTF8",
            )
            self.cursor = self.conn.cursor()

            # Cria as tabelas
            self.criar_tabela("klines")
            self.criar_tabela("analise_candles")
            self.criar_tabela("medias_moveis")
            # ... (chamar a função criar_tabela para outras tabelas) ...

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inicializar o plugin BancoDados: {error}")
            raise

    def finalizar(self):
        """
        Fecha a conexão com o banco de dados.
        """
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logger.info("Conexão com o PostgreSQL fechada.")
