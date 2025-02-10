import time
from typing import List, Tuple, Optional

import psycopg2
from utils.singleton import singleton
from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


@singleton
class BancoDados(Plugin):
    """
    Plugin para gerenciamento do banco de dados.

    Regras de Ouro:
    2 - Criterioso: Validação rigorosa das operações
    3 - Seguro: Tratamento de erros e singleton
    6 - Clareza: Documentação clara
    7 - Modular: Responsabilidade única
    9 - Testável: Métodos bem definidos
    10 - Documentado: Docstrings completos
    """

    # Identificadores do plugin
    PLUGIN_NAME = "banco_dados"
    PLUGIN_TYPE = "essencial"

    _instance = None

    def __new__(cls):
        """Implementa o padrão singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.inicializado = False
        return cls._instance

    def __init__(self):
        """Inicializa o plugin de banco de dados."""
        if not self.inicializado:
            super().__init__()  # This will set nome from PLUGIN_NAME
            self.descricao = "Gerenciamento de banco de dados"
            self._conn = None
            self._config = None

    def conectar(
        self, db_host: str, db_name: str, db_user: str, db_password: str
    ) -> bool:
        """
        Estabelece conexão com o banco de dados.

        Args:
            db_host: Host do banco
            db_name: Nome do banco
            db_user: Usuário
            db_password: Senha

        Returns:
            bool: True se conectado com sucesso
        """
        try:
            self._conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                client_encoding="utf8",
                options="-c client_encoding=utf8",
            )
            self._conn.autocommit = True
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return False

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa a conexão com o banco.

        Args:
            config (dict): Configurações de conexão

        Returns:
            bool: True se inicializado com sucesso

        Raises:
            Exception: Se falhar ao conectar
        """
        try:
            # Inicializa classe base
            super().inicializar(config)
            self._config = config

            # Obtém gerenciador de banco com retry
            max_tentativas = 3
            tentativa = 0
            while tentativa < max_tentativas:
                try:
                    from plugins.gerente_plugin import GerentePlugin

                    gerente = GerentePlugin()
                    gerenciador_banco = gerente.plugins.get("gerenciador_banco")

                    if gerenciador_banco and gerenciador_banco.inicializado:
                        # Usa conexão do gerenciador
                        self._conn = gerenciador_banco._pool
                        if self._conn:
                            self.inicializado = True
                            logger.info("Banco de dados inicializado com sucesso")
                            return True

                    tentativa += 1
                    if tentativa < max_tentativas:
                        logger.warning(
                            f"Tentativa {tentativa}: Aguardando gerenciador_banco... (2s)"
                        )
                        time.sleep(2)
                    else:
                        logger.error(
                            "Gerenciador de banco não disponível após tentativas"
                        )
                        return False

                except Exception as e:
                    logger.error(f"Erro ao obter gerenciador_banco: {e}")
                    return False

        except Exception as e:
            logger.error(f"Erro ao inicializar o banco de dados: {e}")
            return False

    def criar_tabela_klines(self, schema="public"):
        """Cria a tabela klines."""
        try:
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(f"Tabela '{schema}.klines' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'klines': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_analise_candles(self, schema="public"):
        """Cria a tabela analise_candles."""
        try:
            with self._conn.cursor() as cursor:
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
                        UNIQUE (symbol, timeframe, timestamp)
                    );
                    """
                )
                self._conn.commit()
                logger.info(f"Tabela '{schema}.analise_candles' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'analise_candles': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_medias_moveis(self, schema="public"):
        """Cria a tabela medias_moveis."""
        try:
            with self._conn.cursor() as cursor:
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
                        UNIQUE (symbol, timeframe, timestamp)
                    );
                    """
                )
                self._conn.commit()
                logger.info(f"Tabela '{schema}.medias_moveis' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'medias_moveis': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_indicadores_osciladores(self, schema="public"):
        """Cria a tabela indicadores_osciladores."""
        try:
            with self._conn.cursor() as cursor:
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
                        UNIQUE (symbol, timeframe, timestamp, nome_indicador)
                    );
                    """
                )
                self._conn.commit()
                logger.info(
                    f"Tabela '{schema}.indicadores_osciladores' criada com sucesso!"
                )
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_osciladores': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_indicadores_tendencia(self, schema="public"):
        """Cria a tabela indicadores_tendencia."""
        try:
            with self._conn.cursor() as cursor:
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
                        UNIQUE (symbol, timeframe, timestamp, nome_indicador)
                    );
                    """
                )
                self._conn.commit()
                logger.info(
                    f"Tabela '{schema}.indicadores_tendencia' criada com sucesso!"
                )
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_tendencia': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_indicadores_volatilidade(self, schema="public"):
        """Cria a tabela indicadores_volatilidade."""
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE TABLE {schema}.indicadores_volatilidade (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        nome_indicador TEXT NOT NULL,
                        valor REAL,
                        UNIQUE (symbol, timeframe, timestamp, nome_indicador)
                    );
                    """
                )
                self._conn.commit()
                logger.info(
                    f"Tabela '{schema}.indicadores_volatilidade' criada com sucesso!"
                )
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_volatilidade': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_indicadores_volume(self, schema="public"):
        """Cria a tabela indicadores_volume."""
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE TABLE {schema}.indicadores_volume (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        nome_indicador TEXT NOT NULL,
                        valor REAL,
                        UNIQUE (symbol, timeframe, timestamp, nome_indicador)
                    );
                    """
                )
                self._conn.commit()
                logger.info(f"Tabela '{schema}.indicadores_volume' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'indicadores_volume': {error}")
            self._conn.rollback()
            raise

    def criar_tabela_outros_indicadores(self, schema="public"):
        """Cria a tabela outros_indicadores."""
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE TABLE {schema}.outros_indicadores (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        nome_indicador TEXT NOT NULL,
                        valor REAL,
                        UNIQUE (symbol, timeframe, timestamp, nome_indicador)
                    );
                    """
                )
                self._conn.commit()
                logger.info(f"Tabela '{schema}.outros_indicadores' criada com sucesso!")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao criar tabela 'outros_indicadores': {error}")
            self._conn.rollback()
            raise

    def criar_tabela(self, nome_tabela, schema="public"):
        """
        Cria uma tabela no banco de dados se ela não existir.

        Args:
            nome_tabela (str): Nome da tabela a ser criada.
            schema (str): Nome do schema onde a tabela será criada (padrão: "public").

        Raises:
            ValueError: Se o nome da tabela for inválido
            psycopg2.Error: Se houver erro ao criar a tabela
        """
        try:
            with self._conn.cursor() as cursor:
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
                tabela_existe = cursor.fetchone()[0]

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
                        self._conn.commit()
                        logger.info(
                            f"Tabela '{schema}.{nome_tabela}' criada com sucesso!"
                        )
                    else:
                        logger.error(f"Nome de tabela inválido: {nome_tabela}")
                        raise ValueError(f"Nome de tabela inválido: {nome_tabela}")

        except psycopg2.Error as e:
            logger.error(f"Erro ao criar tabela '{schema}.{nome_tabela}': {e}")
            self._conn.rollback()
            raise

    def buscar_dados(self, tabela, condicao=""):
        """
        Busca dados em uma tabela do banco de dados.

        Args:
            tabela (str): O nome da tabela.
            condicao (str, opcional): A condição para a busca (cláusula WHERE).

        Returns:
            list: Uma lista de tuplas com os resultados da busca.

        Raises:
            psycopg2.Error: Se houver erro ao executar a consulta
        """
        try:
            with self._conn.cursor() as cursor:
                sql = f"SELECT * FROM {tabela}"
                if condicao:
                    sql += f" WHERE {condicao}"
                cursor.execute(sql)
                return cursor.fetchall()

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao buscar dados na tabela {tabela}: {error}")
            return []  # Retorna uma lista vazia em caso de erro

    def validar_dados_klines(self, dados: List[Tuple]) -> bool:
        """
        Valida o formato dos dados de klines antes da inserção.

        Args:
            dados: Lista de tuplas com dados de klines

        Returns:
            bool: True se os dados são válidos

        Raises:
            ValueError: Se os dados estiverem inválidos
        """
        if not dados:
            raise ValueError("Lista de dados vazia")

        for dado in dados:
            if len(dado) != 8:
                raise ValueError(f"Formato inválido: {dado}")

            if not all(isinstance(x, (str, int, float)) for x in dado):
                raise ValueError(f"Tipos inválidos: {dado}")

        return True

    def inserir_dados_klines(self, dados: List[Tuple]) -> None:
        """
        Insere dados de klines no banco de dados.

        Args:
            dados: Lista de tuplas contendo (symbol, timeframe, timestamp, open, high, low, close, volume)

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados

        Examples:
            >>> db.inserir_dados_klines([
            ...     ("BTC/USDT:USDT", "1h", 1643673600, 42000.0, 42100.0, 41900.0, 42050.0, 100.0)
            ... ])
        """
        if not isinstance(dados, list):
            raise ValueError("Dados deve ser uma lista de tuplas")

        try:
            # Normaliza os symbols nos dados
            dados_normalizados = [(normalizar_symbol(d[0]), *d[1:]) for d in dados]

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

            with self._conn.cursor() as cursor:
                cursor.executemany(query, dados_normalizados)
                self._conn.commit()
                logger.info(f"Inseridos {len(dados)} registros de klines com sucesso")

        except Exception as erro:
            logger.error(f"Erro ao inserir dados na tabela klines: {str(erro)}")
            self._conn.rollback()
            raise

    def inserir_dados_analise_candles(self, dados):
        """
        Insere dados na tabela analise_candles.

        Args:
            dados (dict): Dicionário com os dados da análise
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "padrao": str,
                    "classificacao": str,
                    "sinal": str,
                    "stop_loss": float,
                    "take_profit": float
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO analise_candles (symbol, timeframe, timestamp, padrao, classificacao, sinal, stop_loss, take_profit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
                SET padrao = EXCLUDED.padrao, 
                    classificacao = EXCLUDED.classificacao,
                    sinal = EXCLUDED.sinal, 
                    stop_loss = EXCLUDED.stop_loss, 
                    take_profit = EXCLUDED.take_profit;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela analise_candles para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela analise_candles: {error}")
            self._conn.rollback()
            raise

    def inserir_dados_medias_moveis(self, dados):
        """
        Insere dados na tabela medias_moveis.

        Args:
            dados (dict): Dicionário com os dados das médias móveis
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "sinal": str,
                    "stop_loss": float,
                    "take_profit": float
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO medias_moveis (symbol, timeframe, timestamp, sinal, stop_loss, take_profit)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
                SET sinal = EXCLUDED.sinal,
                    stop_loss = EXCLUDED.stop_loss,
                    take_profit = EXCLUDED.take_profit;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela medias_moveis para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela medias_moveis: {error}")
            self._conn.rollback()
            raise

    def inserir_dados_indicadores_osciladores(self, dados):
        """
        Insere dados na tabela indicadores_osciladores.

        Args:
            dados (dict): Dicionário com os dados dos indicadores
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "nome_indicador": str,
                    "valor": float,
                    "sinal": str
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO indicadores_osciladores (symbol, timeframe, timestamp, nome_indicador, valor, sinal)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor, sinal = EXCLUDED.sinal;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela indicadores_osciladores para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(
                f"Erro ao inserir dados na tabela indicadores_osciladores: {error}"
            )
            self._conn.rollback()
            raise

    def inserir_dados_indicadores_tendencia(self, dados):
        """
        Insere dados na tabela indicadores_tendencia.

        Args:
            dados (dict): Dicionário com os dados dos indicadores
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "nome_indicador": str,
                    "valor": float,
                    "sinal": str
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO indicadores_tendencia (symbol, timeframe, timestamp, nome_indicador, valor, sinal)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor, sinal = EXCLUDED.sinal;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela indicadores_tendencia para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(
                f"Erro ao inserir dados na tabela indicadores_tendencia: {error}"
            )
            self._conn.rollback()
            raise

    def inserir_dados_indicadores_volatilidade(self, dados):
        """
        Insere dados na tabela indicadores_volatilidade.

        Args:
            dados (dict): Dicionário com os dados dos indicadores
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "nome_indicador": str,
                    "valor": float
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO indicadores_volatilidade (symbol, timeframe, timestamp, nome_indicador, valor)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela indicadores_volatilidade para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(
                f"Erro ao inserir dados na tabela indicadores_volatilidade: {error}"
            )
            self._conn.rollback()
            raise

    def inserir_dados_indicadores_volume(self, dados):
        """
        Insere dados na tabela indicadores_volume.

        Args:
            dados (dict): Dicionário com os dados dos indicadores
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "nome_indicador": str,
                    "valor": float
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO indicadores_volume (symbol, timeframe, timestamp, nome_indicador, valor)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela indicadores_volume para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela indicadores_volume: {error}")
            self._conn.rollback()
            raise

    def inserir_dados_outros_indicadores(self, dados):
        """
        Insere dados na tabela outros_indicadores.

        Args:
            dados (dict): Dicionário com os dados dos indicadores
                {
                    "symbol": str,
                    "timeframe": str,
                    "timestamp": int,
                    "nome_indicador": str,
                    "valor": float
                }

        Raises:
            ValueError: Se os dados não estiverem no formato esperado
            psycopg2.Error: Se houver erro no banco de dados
        """
        try:
            dados["symbol"] = normalizar_symbol(dados["symbol"])
            sql = """
                INSERT INTO outros_indicadores (symbol, timeframe, timestamp, nome_indicador, valor)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timeframe, timestamp, nome_indicador) DO UPDATE
                SET valor = EXCLUDED.valor;
            """
            with self._conn.cursor() as cursor:
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
                self._conn.commit()
                logger.info(
                    f"Dados inseridos com sucesso na tabela outros_indicadores para {dados['symbol']}"
                )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao inserir dados na tabela outros_indicadores: {error}")
            self._conn.rollback()
            raise

    def inserir_dados(self, tabela: str, dados: dict) -> bool:
        """
        Insere dados em uma tabela do banco de dados, evitando duplicidades.

        Args:
            tabela: O nome da tabela
            dados: Os dados a serem inseridos

        Returns:
            bool: True se inserido com sucesso
        """
        try:
            # Valida se é par USDT
            if "symbol" in dados and not self.validar_par_usdt(dados["symbol"]):
                logger.warning(f"Par ignorado (não USDT): {dados['symbol']}")
                return False

            # Obtém gerenciador de banco
            from plugins.gerente_plugin import GerentePlugin

            gerente = GerentePlugin()
            gerenciador_banco = gerente.plugins.get("gerenciador_banco")

            if not gerenciador_banco:
                raise Exception("Gerenciador de banco não encontrado")

            # Usa conexão do gerenciador
            self._conn = gerenciador_banco._pool

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
            else:
                logger.error(f"Tabela inválida: {tabela}")
                return False

            return True

        except Exception as error:
            logger.error(f"Erro ao inserir dados na tabela {tabela}: {error}")
            return False

    def validar_par_usdt(self, symbol: str) -> bool:
        """
        Valida se o par termina em USDT.

        Args:
            symbol: Par a ser validado

        Returns:
            bool: True se o par é válido
        """
        return symbol.endswith("USDT")

    def criar_tabelas(self) -> None:
        """
        Cria as tabelas necessárias se não existirem.

        Raises:
            psycopg2.Error: Se houver erro ao criar as tabelas
        """
        try:
            # Obtém gerenciador de banco
            from plugins.gerente_plugin import GerentePlugin

            gerente = GerentePlugin()
            gerenciador_banco = gerente.plugins.get("gerenciador_banco")

            if not gerenciador_banco:
                raise Exception("Gerenciador de banco não encontrado")

            # Usa conexão do gerenciador
            self._conn = gerenciador_banco._pool

            # Cria tabelas através do gerenciador
            tabelas = [
                "klines",
                "analise_candles",
                "medias_moveis",
                "indicadores_osciladores",
                "indicadores_tendencia",
                "indicadores_volatilidade",
                "indicadores_volume",
                "outros_indicadores",
            ]

            for tabela in tabelas:
                gerenciador_banco.criar_tabela(tabela)

            logger.info("Tabelas criadas/verificadas com sucesso")

        except Exception as erro:
            logger.error(f"Erro ao criar tabelas: {str(erro)}")
            if self._conn:
                self._conn.rollback()
            raise

    def finalizar(self):
        """
        Fecha a conexão com o banco de dados.

        Raises:
            Exception: Se houver erro ao fechar a conexão
        """
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
                logger.info("Conexão com o banco de dados fechada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao fechar conexão com banco: {e}")
            raise


def normalizar_symbol(symbol: str) -> str:
    """
    Normaliza o formato do símbolo para o padrão do banco de dados.

    Args:
        symbol (str): Símbolo no formato original (ex: "BTC/USDT:USDT")

    Returns:
        str: Símbolo normalizado (ex: "BTCUSDT")

    Examples:
        >>> normalizar_symbol("BTC/USDT:USDT")
        'BTCUSDT'
        >>> normalizar_symbol("ETH/USDT")
        'ETHUSDT'
    """
    return symbol.replace("/", "").replace(":USDT", "")
