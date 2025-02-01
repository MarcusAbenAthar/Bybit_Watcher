from venv import logger
import psycopg2
from plugins.plugin import Plugin


class BancoDados(Plugin):
    """
    Plugin para gerenciar o banco de dados PostgreSQL.

    Este plugin é responsável por estabelecer a conexão com o banco de dados,
    criar as tabelas necessárias e executar operações de busca e inserção de dados.
    """

    def __init__(self):
        """
        Inicializa o plugin BancoDados.
        """
        super().__init__()
        self.conn = None  # Inicializa a conexão como None

    def inicializar(self, config):
        """
        Estabelece a conexão com o banco de dados PostgreSQL.
        Args:
            config (ConfigParser): Objeto com as configurações do bot.
        """
        try:
            # Obtém as configurações do objeto config
            db_host = config.get("database", "host")
            db_name = config.get("database", "database")
            db_user = config.get("database", "user")
            db_password = config.get("database", "password")

            self.conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
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
            cursor = self.conn.cursor()  # Obtém o cursor da conexão

            # Verifica se a tabela já existe
            logger.info(
                f"Verificando se a tabela '{schema}.{nome_tabela}' já existe..."
            )
            cursor.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}'
                    AND table_name = '{nome_tabela}'
                );
                """
            )
            tabela_existe = cursor.fetchone()

            if not tabela_existe:
                # Cria a tabela
                logger.info(f"Criando a tabela '{schema}.{nome_tabela}'...")
                if nome_tabela == "klines":
                    cursor.execute(
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
                    cursor.execute(
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
                    cursor.execute(
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
                # ... (adicionar código para criar outras tabelas)...

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
            return

    def inserir_dados(self, tabela, dados):
        """
        Insere dados em uma tabela do banco de dados.
        Args:
            tabela (str): O nome da tabela.
            dados (dict): Os dados a serem inseridos.
        """
        try:
            cursor = self.conn.cursor()
            colunas = ", ".join(dados.keys())
            valores = ", ".join(["%s"] * len(dados))
            sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({valores})"
            cursor.execute(sql, tuple(dados.values()))
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela {tabela}: {error}")

    def finalizar(self):
        """
        Fecha a conexão com o banco de dados.
        """
        if self.conn:  # Verifica se a conexão existe antes de tentar fechá-la
            self.conn.close()
            logger.info("Conexão com o PostgreSQL fechada.")
