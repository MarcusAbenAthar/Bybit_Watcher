import configparser

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

    def inicializar(self, plugins):
        """
        Conecta ao banco de dados e cria a tabela `klines` se ela não existir.
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

            # Verifica se a tabela `klines` já existe
            logger.info("Verificando se a tabela `klines` já existe...")
            self.cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'klines'
                );
                """
            )
            tabela_existe = self.cursor.fetchone()[0]

            if not tabela_existe:
                # Cria a tabela `klines` com a restrição de unicidade
                logger.info("Criando a tabela `klines`...")
                self.cursor.execute(
                    """
                    CREATE TABLE public.klines (
                        id SERIAL PRIMARY KEY,
                        par TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        UNIQUE (par, timeframe, timestamp)  -- Restrição de unicidade
                    );

                    ALTER TABLE IF EXISTS public.klines
                        OWNER to marcus;
                    """
                )
                self.conn.commit()
                logger.info("Tabela `klines` criada com sucesso!")
            else:
                logger.info("Tabela `klines` já existe.")
            if not tabela_existe:
                # Cria a tabela `analise_candles`
                logger.info("Criando a tabela `analise_candles`...")
                self.cursor.execute(
                    """
                    CREATE TABLE public.analise_candles (
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

                    ALTER TABLE IF EXISTS public.analise_candles
                        OWNER to postgres;
                    """
                )
                self.conn.commit()
                logger.info("Tabela `analise_candles` criada com sucesso!")
            else:
                logger.info("Tabela `analise_candles` já existe.")

        except psycopg2.OperationalError as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
            raise

        except psycopg2.ProgrammingError as e:
            logger.error(f"Erro na consulta SQL: {e}")
            raise

        except Exception as e:
            logger.error(f"Erro genérico: {e}")
            raise

    def finalizar(self):
        """
        Fecha a conexão com o banco de dados.
        """
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logger.info("Conexão com o PostgreSQL fechada.")
