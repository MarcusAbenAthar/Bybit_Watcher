import psycopg2
import logging

logger = logging.getLogger(__name__)
from plugins.plugin import Plugin
from typing import List, Tuple


class BancoDados(Plugin):
    """
    Plugin para gerenciar o banco de dados PostgreSQL.

    Este plugin é responsável por estabelecer a conexão com o banco de dados,
    criar as tabelas necessárias e executar operações de busca e inserção de dados.
    """

    def __init__(self, config):
        """Inicializa o plugin BancoDados."""
        super().__init__()
        self.nome = "Banco de Dados"
        self.config = config
        self.conectar(
            config.get("database", "database"),
            config.get("database", "user"),
            config.get("database", "password"),
            config.get("database", "host"),
        )

    def conectar(self, db_name, db_user, db_password, db_host="localhost"):
        """
        Estabelece a conexão com o banco de dados PostgreSQL.

        Args:
            db_name (str): Nome do banco de dados.
            db_user (str): Nome do usuário do banco de dados.
            db_password (str): Senha do usuário do banco de dados.
            db_host (str): Host do banco de dados.
        """
        try:
            self.conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                client_encoding="utf8",
            )
            logger.info(
                f"Conexão com o banco de dados '{db_name}' estabelecida com sucesso."
            )
            return self.conn  # Retorna a conexão estabelecida

        except psycopg2.OperationalError as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
            raise

        except Exception as e:
            # Registra a exceção original com logger.exception()
            logger.exception(f"Erro ao conectar ao banco de dados: {e}")

    def inicializar(self, config):
        """
        Inicializa o banco de dados, criando-o se não existir e estabelecendo a conexão.

        Args:
            config (ConfigParser): Objeto com as configurações do bot.
        """
        try:
            # Obtém as configurações do objeto config
            db_host = config.get("database", "host")
            db_name = config.get("database", "database")
            db_user = config.get("database", "user")
            db_password = config.get("database", "password")

            # Cria o banco de dados se ele não existir
            self.criar_banco_dados(db_name, db_user, db_password)

            # Conecta ao banco de dados
            self.conectar(db_name, db_user, db_password, db_host)

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inicializar o banco de dados: {error}")
            raise

        return self.conn  # Retorna a conexão estabelecida

    def criar_banco_dados(self, db_name, db_user, db_password):
        """
        Cria o banco de dados se ele não existir.

        Args:
            db_name (str): Nome do banco de dados.
            db_user (str): Nome do usuário do banco de dados.
            db_password (str): Senha do usuário do banco de dados.
        """
        try:
            # Conecta ao banco de dados padrão (postgres)
            conn = self.conectar("postgres", db_user, db_password)
            conn.autocommit = True
            cursor = conn.cursor()

            # Verifica se o banco de dados já existe
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            banco_existe = cursor.fetchone()

            if not banco_existe:
                # Cria o banco de dados
                logger.info(f"Criando o banco de dados '{db_name}'...")
                cursor.execute(f"CREATE DATABASE {db_name}")
                logger.info(f"Banco de dados '{db_name}' criado com sucesso!")
            cursor.close()

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar banco de dados '{db_name}': {error}")
            raise

    def criar_tabela_klines(self, schema="public"):
        """Cria a tabela klines."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.klines (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    UNIQUE (symbol, timeframe, timestamp)
                );
                """
            )
            self.conn.commit()
            logger.info(f"Tabela '{schema}.klines' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'klines': {error}")
            raise

    def criar_tabela_analise_candles(self, schema="public"):
        """Cria a tabela analise_candles."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.analise_candles (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    padrao TEXT,
                    classificacao TEXT,
                    sinal TEXT,
                    stop_loss REAL,
                    take_profit REAL,
                    UNIQUE (symbol timeframe, timestamp)
                );
                """
            )
            self.conn.commit()
            logger.info(f"Tabela '{schema}.analise_candles' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'analise_candles': {error}")
            raise

    def criar_tabela_medias_moveis(self, schema="public"):
        """Cria a tabela medias_moveis."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.medias_moveis (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    sinal TEXT,
                    stop_loss REAL,
                    take_profit REAL,
                    UNIQUE (symbol timeframe, timestamp)
                );
                """
            )
            self.conn.commit()
            logger.info(f"Tabela '{schema}.medias_moveis' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'medias_moveis': {error}")
            raise

    def criar_tabela_indicadores_osciladores(self, schema="public"):
        """Cria a tabela indicadores_osciladores."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.indicadores_osciladores (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    nome_indicador TEXT NOT NULL,
                    valor REAL,
                    sinal TEXT,
                    UNIQUE (symbol timeframe, timestamp, nome_indicador)
                );
                """
            )
            self.conn.commit()
            logger.info(
                f"Tabela '{schema}.indicadores_osciladores' criada com sucesso!"
            )
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_osciladores': {error}")
            raise

    def criar_tabela_indicadores_tendencia(self, schema="public"):
        """Cria a tabela indicadores_tendencia."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.indicadores_tendencia (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    nome_indicador TEXT NOT NULL,
                    valor REAL,
                    sinal TEXT,
                    UNIQUE (symbol timeframe, timestamp, nome_indicador)
                );
                """
            )
            self.conn.commit()
            logger.info(f"Tabela '{schema}.indicadores_tendencia' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_tendencia': {error}")
            raise

    def criar_tabela_indicadores_volatilidade(self, schema="public"):
        """Cria a tabela indicadores_volatilidade."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.indicadores_volatilidade (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    nome_indicador TEXT NOT NULL,
                    valor REAL,
                    UNIQUE (symbol timeframe, timestamp, nome_indicador)
                );
                """
            )
            self.conn.commit()
            logger.info(
                f"Tabela '{schema}.indicadores_volatilidade' criada com sucesso!"
            )
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_volatilidade': {error}")
            raise

    def criar_tabela_indicadores_volume(self, schema="public"):
        """Cria a tabela indicadores_volume."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.indicadores_volume (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    nome_indicador TEXT NOT NULL,
                    valor REAL,
                    UNIQUE (symbol timeframe, timestamp, nome_indicador)
                );
                """
            )
            self.conn.commit()
            logger.info(f"Tabela '{schema}.indicadores_volume' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_volume': {error}")
            raise

    def criar_tabela_outros_indicadores(self, schema="public"):
        """Cria a tabela outros_indicadores."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE {schema}.outros_indicadores (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp BIGINT NOT NULL,
                    nome_indicador TEXT NOT NULL,
                    valor REAL,
                    UNIQUE (symbol timeframe, timestamp, nome_indicador)
                );
                """
            )
            self.conn.commit()
            logger.info(f"Tabela '{schema}.outros_indicadores' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'outros_indicadores': {error}")
            raise

    def criar_tabela(self, nome_tabela, schema="public"):
        """
        Cria uma tabela no banco de dados se ela não existir.

        Args:
            nome_tabela (str): Nome da tabela a ser criada.
            schema (str): Nome do schema onde a tabela será criada (padrão: "public").
        """
        try:
            cursor = self.conn.cursor()

            # Verifica se a tabela já existe no banco de dados
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                )
                """,
                (schema, nome_tabela),
            )
            tabela_existe = cursor.fetchone()[
                0
            ]  # Correção: Captura o valor booleano corretamente

            if not tabela_existe:
                logger.info(f"Criando a tabela '{schema}.{nome_tabela}'...")

                # Chama a função específica para criar a tabela com base no nome
                funcoes_criacao = {
                    "klines": self.criar_tabela_klines,
                    "analise_candles": self.criar_tabela_analise_candles,
                    "medias_moveis": self.criar_tabela_medias_moveis,
                    "indicadores_osciladores": self.criar_tabela_indicadores_osciladores,
                    "indicadores_tendencia": self.criar_tabela_indicadores_tendencia,
                    "indicadores_volatilidade": self.criar_tabela_indicadores_volatilidade,
                    "indicadores_volume": self.criar_tabela_indicadores_volume,
                    "outros_indicadores": self.criar_tabela_outros_indicadores,
                }

                funcao_criacao = funcoes_criacao.get(nome_tabela)
                if funcao_criacao:
                    funcao_criacao(schema)
                    self.conn.commit()
                    logger.info(f"Tabela '{schema}.{nome_tabela}' criada com sucesso!")
                else:
                    logger.error(f"Nome de tabela inválido: {nome_tabela}")
                    raise ValueError(f"Nome de tabela inválido: {nome_tabela}")

        except psycopg2.Error as e:
            logger.error(f"Erro ao criar tabela '{schema}.{nome_tabela}': {e}")
            self.conn.rollback()  # Correção: Garante que a transação não fique em estado inválido
            raise
        finally:
            cursor.close()  # Correção: Fecha o cursor para evitar vazamento de conexões

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
            return  # Retorna uma lista vazia em caso de erro

    def inserir_dados_klines(self, dados: List[Tuple]) -> None:
        """
        Insere dados de klines no banco de dados.

        Args:
            dados: Lista de tuplas contendo (symbol, timeframe, timestamp, open, high, low, close, volume)
        """
        try:
            query = """
                INSERT INTO klines (symbol, timeframe, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp)
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
            """

            # Verifica se dados é uma lista de tuplas
            if not isinstance(dados, list):
                raise ValueError("Dados deve ser uma lista de tuplas")

            # Executa a query para cada linha de dados
            with self.conn.cursor() as cursor:
                cursor.executemany(query, dados)

            self.conn.commit()

        except Exception as erro:
            logger.error(f"Erro ao inserir dados na tabela klines: {str(erro)}")
            self.conn.rollback()
            raise

    def inserir_dados_analise_candles(self, dados):
        """Insere dados na tabela analise_candles."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO analise_candles (symbol timeframe, timestamp, padrao, classificacao, sinal, stop_loss, take_profit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp) DO UPDATE
                SET padrao = EXCLUDED.padrao, classificacao = EXCLUDED.classificacao,
                    sinal = EXCLUDED.sinal, stop_loss = EXCLUDED.stop_loss, take_profit = EXCLUDED.take_profit;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["padrao"],
                    dados["classificacao"],
                    dados["sinal"],
                    dados["stop_loss"],
                    dados["take_profit"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela analise_candles: {error}")

    def inserir_dados_medias_moveis(self, dados):
        """Insere dados na tabela medias_moveis."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO medias_moveis (symbol timeframe, timestamp, sinal, stop_loss, take_profit)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp) DO UPDATE
                SET sinal = EXCLUDED.sinal, stop_loss = EXCLUDED.stop_loss, take_profit = EXCLUDED.take_profit;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["sinal"],
                    dados["stop_loss"],
                    dados["take_profit"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela medias_moveis: {error}")

    def inserir_dados_indicadores_osciladores(self, dados):
        """Insere dados na tabela indicadores_osciladores."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO indicadores_osciladores (symbol timeframe, timestamp, nome_indicador, valor, sinal)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor, sinal = EXCLUDED.sinal;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["nome_indicador"],
                    dados["valor"],
                    dados["sinal"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(
                f"Erro ao inserir dados na tabela indicadores_osciladores: {error}"
            )

    def inserir_dados_indicadores_tendencia(self, dados):
        """Insere dados na tabela indicadores_tendencia."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO indicadores_tendencia (symbol timeframe, timestamp, nome_indicador, valor, sinal)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor, sinal = EXCLUDED.sinal;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["nome_indicador"],
                    dados["valor"],
                    dados["sinal"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(
                f"Erro ao inserir dados na tabela indicadores_tendencia: {error}"
            )

    def inserir_dados_indicadores_volatilidade(self, dados):
        """Insere dados na tabela indicadores_volatilidade."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO indicadores_volatilidade (symbol timeframe, timestamp, nome_indicador, valor)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["nome_indicador"],
                    dados["valor"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(
                f"Erro ao inserir dados na tabela indicadores_volatilidade: {error}"
            )

    def inserir_dados_indicadores_volume(self, dados):
        """Insere dados na tabela indicadores_volume."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO indicadores_volume (symbol timeframe, timestamp, nome_indicador, valor)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["nome_indicador"],
                    dados["valor"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela indicadores_volume: {error}")

    def inserir_dados_outros_indicadores(self, dados):
        """Insere dados na tabela outros_indicadores."""
        try:
            cursor = self.conn.cursor()
            sql = f"""
                INSERT INTO outros_indicadores (symbol timeframe, timestamp, nome_indicador, valor)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor;
            """
            cursor.execute(
                sql,
                (
                    dados["symbol"],
                    dados["timeframe"],
                    dados["timestamp"],
                    dados["nome_indicador"],
                    dados["valor"],
                ),
            )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela outros_indicadores: {error}")

    def inserir_dados(self, tabela, dados):
        """
        Insere dados em uma tabela do banco de dados, evitando duplicidades.

        Args:
            tabela (str): O nome da tabela.
            dados (dict): Os dados a serem inseridos.
        """
        try:
            # Chama a função específica para inserir dados na tabela
            if tabela == "klines":
                self.inserir_dados_klines(dados)
            elif tabela == "analise_candles":
                self.inserir_dados_analise_candles(dados)
            elif tabela == "medias_moveis":
                self.inserir_dados_medias_moveis(dados)
            elif tabela == "indicadores_osciladores":
                self.inserir_dados_indicadores_osciladores(dados)
            elif tabela == "indicadores_tendencia":
                self.inserir_dados_indicadores_tendencia(dados)
            elif tabela == "indicadores_volatilidade":
                self.inserir_dados_indicadores_volatilidade(dados)
            elif tabela == "indicadores_volume":
                self.inserir_dados_indicadores_volume(dados)
            elif tabela == "outros_indicadores":
                self.inserir_dados_outros_indicadores(dados)

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela {tabela}: {error}")

    def criar_tabelas(self) -> None:
        """Cria as tabelas necessárias se não existirem."""
        try:
            with self.conn.cursor() as cursor:
                # Tabela de sinais
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sinais (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(50) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        tipo VARCHAR(50) NOT NULL,
                        sinal VARCHAR(20) NOT NULL,
                        confianca FLOAT NOT NULL,
                        stop_loss FLOAT,
                        take_profit FLOAT,
                        timestamp BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_sinais_symbol_timeframe 
                    ON sinais(symbol, timeframe);
                """
                )

                self.conn.commit()
                logger.info("Tabelas criadas/verificadas com sucesso")

        except Exception as erro:
            logger.error(f"Erro ao criar tabelas: {str(erro)}")
            self.conn.rollback()
            raise

    def finalizar(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            logger.info("Conexão com o PostgreSQL fechada.")
