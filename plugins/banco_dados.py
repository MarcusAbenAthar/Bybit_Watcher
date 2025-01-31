import configparser
from venv import logger

import psycopg2
from trading_core import Core
from plugins.plugin import Plugin


class BancoDados(Plugin):
    """
    Plugin para gerenciar o banco de dados PostgreSQL, agora integrado com o Core.
    """

    def __init__(self, core):
        super().__init__(core)
        self.conn = None  # Inicializa a conexão como None

    def inicializar(self):
        try:
            db_host = self.core.config.get("database", "host")
            db_name = self.core.config.get("database", "name")
            db_user = self.core.config.get("database", "user")
            db_password = self.core.config.get("database", "password")

            self.conn = psycopg2.connect(
                host=db_host, database=db_name, user=db_user, password=db_password
            )
            logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao conectar ao banco de dados: {error}")
            raise

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

    def buscar_dados(self, tabela, condicao=""):
        """
        Busca dados em uma tabela do banco de dados.

        Args:
            tabela (str): O nome da tabela.
            condicao (str, opcional): A condição para a busca (cláusula WHERE).

        Returns:
            list: Uma lista de tuplas com os resultados da busca.
        """
        try:
            cursor = self.conn.cursor()
            sql = f"SELECT * FROM {tabela}"
            if condicao:
                sql += f" WHERE {condicao}"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            cursor.close()
            return resultados
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao buscar dados na tabela {tabela}: {error}")
            return []

    def finalizar(self):
        """
        Fecha a conexão com o banco de dados.
        """
        logger.info("Conexão com o PostgreSQL fechada.")
