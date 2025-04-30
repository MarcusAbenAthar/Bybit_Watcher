import os
import pytest
from utils.config import carregar_config
from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.banco_dados import BancoDados


def setup_module(module):
    # Override .pgpass para evitar problemas de encoding
    import tempfile
    tmp_pgpass = tempfile.NamedTemporaryFile(delete=False)
    tmp_pgpass.close()
    os.environ['PGPASSFILE'] = tmp_pgpass.name

    # Limpa registro de tabelas
    registry = getattr(BancoDados, 'registry', None)
    if registry is not None:
        registry.clear()


def test_gerenciador_banco_e_banco_dados_crud():
    """
    Testa inicialização, registro de tabela e CRUD usando GerenciadorBanco e BancoDados.
    O CRUD é feito usando a conexão exposta pelo gerenciador, garantindo modularidade e testabilidade.
    """
    config = carregar_config()
    # Inicializa o gerenciador e o plugin de banco
    gb = GerenciadorBanco()
    assert gb.inicializar(config), "Falha ao inicializar GerenciadorBanco"
    plugin_bd = BancoDados(gerenciador_banco=gb)
    assert plugin_bd.inicializar(config), "Falha ao inicializar BancoDados"

    # Verifica registro de tabela
    tabelas = BancoDados.get_tabelas_por_plugin()
    assert 'banco_dados' in tabelas and 'dados' in tabelas[
        'banco_dados'], "Tabela 'dados' não registrada pelo BancoDados"

    # CRUD via conexão do gerenciador
    conn = gb.conn
    assert conn is not None and not conn.closed, "Conexão não está ativa"
    cur = conn.cursor()
    table_name = "test_crud_plugin"
    try:
        # Limpa tabela
        cur.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
        # Cria tabela
        cur.execute(
            f"CREATE TABLE {table_name} (id SERIAL PRIMARY KEY, nome TEXT);")
        conn.commit()
        # CREATE
        cur.execute(
            f"INSERT INTO {table_name} (nome) VALUES (%s) RETURNING id;", ("Alice",))
        id_ = cur.fetchone()[0]
        conn.commit()
        # READ
        cur.execute(f"SELECT nome FROM {table_name} WHERE id = %s;", (id_,))
        nome = cur.fetchone()[0]
        assert nome == "Alice", "Leitura falhou após inserção"
        # UPDATE
        cur.execute(
            f"UPDATE {table_name} SET nome = %s WHERE id = %s;", ("Bob", id_))
        conn.commit()
        cur.execute(f"SELECT nome FROM {table_name} WHERE id = %s;", (id_,))
        nome2 = cur.fetchone()[0]
        assert nome2 == "Bob", "Update falhou"
        # DELETE
        cur.execute(f"DELETE FROM {table_name} WHERE id = %s;", (id_,))
        conn.commit()
        cur.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE id = %s;", (id_,))
        count = cur.fetchone()[0]
        assert count == 0, "Delete falhou"
    finally:
        # Limpeza final
        cur.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
        cur.close()
        gb.finalizar()
        plugin_bd.finalizar()


"""
Teste integrado do GerenciadorBanco com PostgreSQL real.
Verifica:
1. Conexão com o banco usando config.py
2. Registro de tabelas via BancoDados
3. Operações CRUD completas
"""
"""
DICA: Para visualizar os prints deste teste no console, execute:
    pytest -s tests/test_gerenciador_banco_e_banco_dados.py -v
Assim, todas as etapas do CRUD e da conexão serão mostradas no terminal.
"""
import os
import pytest
import psycopg2
from utils.config import carregar_config
from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.banco_dados import BancoDados

# Configuração do ambiente de teste
TEST_DB_NAME = "bybit_watcher_test"

def setup_module(module):
    """Prepara ambiente para testes com PostgreSQL"""
    # Garante que as variáveis de ambiente estão carregadas
    config = carregar_config()
    
    # Cria banco de testes se não existir
    conn = psycopg2.connect(
        host=config['db']['host'],
        user=config['db']['user'],
        password=config['db']['password'],
        dbname="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    except psycopg2.errors.DuplicateDatabase:
        pass
    finally:
        cur.close()
        conn.close()

    # Atualiza config para usar o banco de testes
    os.environ['DB_NAME'] = TEST_DB_NAME

    # Limpa registro de tabelas
    registry = getattr(BancoDados, 'registry', None)
    if registry is not None:
        registry.clear()

@pytest.fixture
def test_config():
    """Retorna configuração com banco de testes"""
    config = carregar_config()
    config['db']['database'] = TEST_DB_NAME
    return config

def test_conexao_postgresql_crud_completo(test_config):
    """
    Teste completo de conexão PostgreSQL e CRUD:
    1. Inicializa GerenciadorBanco
    2. Registra tabela via BancoDados
    3. Executa operações CRUD
    """
    # 1. Inicialização
    print("[INÍCIO] Inicializando GerenciadorBanco...")
    gb = GerenciadorBanco()
    assert gb.inicializar(test_config), "Falha na inicialização do GerenciadorBanco"
    print("[OK] GerenciadorBanco inicializado!")
    
    print("[INÍCIO] Inicializando plugin BancoDados...")
    plugin_bd = BancoDados(gerenciador_banco=gb)
    assert plugin_bd.inicializar(test_config), "Falha na inicialização do BancoDados"
    print("[OK] Plugin BancoDados inicializado!")
    
    print("[VERIFICAÇÃO] Checando registro de tabelas...")
    tabelas = BancoDados.get_tabelas_por_plugin()
    assert 'banco_dados' in tabelas, "Plugin não registrado"
    assert 'dados' in tabelas['banco_dados'], "Tabela padrão não registrada"
    print(f"[OK] Registro de tabelas: {tabelas}")
    
    print("[INÍCIO] Testando operações CRUD no PostgreSQL...")
    conn = gb.conn
    assert not conn.closed, "Conexão não está ativa"
    
    table_name = "test_crud"
    cur = conn.cursor()
    
    try:
        print(f"[SETUP] Criando tabela temporária '{table_name}'...")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                valor NUMERIC
            )
        """)
        conn.commit()
        print("[OK] Tabela criada!")
        
        # CREATE
        print("[CREATE] Inserindo registro...")
        cur.execute(
            f"INSERT INTO {table_name} (nome, valor) VALUES (%s, %s) RETURNING id",
            ("Teste", 100.50)
        )
        id_registro = cur.fetchone()[0]
        conn.commit()
        print(f"[OK] Registro inserido com id {id_registro}")
        assert id_registro > 0, "Falha ao inserir registro"
        
        # READ
        print("[READ] Lendo registro...")
        cur.execute(f"SELECT nome, valor FROM {table_name} WHERE id = %s", (id_registro,))
        registro = cur.fetchone()
        print(f"[OK] Registro lido: {registro}")
        assert registro == ("Teste", 100.50), "Falha ao ler registro"
        
        # UPDATE
        print("[UPDATE] Atualizando registro...")
        cur.execute(
            f"UPDATE {table_name} SET nome = %s, valor = %s WHERE id = %s",
            ("Teste Atualizado", 200.75, id_registro)
        )
        conn.commit()
        cur.execute(f"SELECT nome, valor FROM {table_name} WHERE id = %s", (id_registro,))
        registro_atualizado = cur.fetchone()
        print(f"[OK] Registro atualizado: {registro_atualizado}")
        assert registro_atualizado == ("Teste Atualizado", 200.75), "Falha ao atualizar"
        
        # DELETE
        print("[DELETE] Removendo registro...")
        cur.execute(f"DELETE FROM {table_name} WHERE id = %s", (id_registro,))
        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = %s", (id_registro,))
        count = cur.fetchone()[0]
        print(f"[OK] Registros restantes com id {id_registro}: {count}")
        assert count == 0, "Falha ao deletar registro"
        
    finally:
        print(f"[CLEANUP] Removendo tabela temporária '{table_name}'...")
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        cur.close()
        gb.finalizar()
        print("[OK] Limpeza e finalização concluídas!")
    
    assert conn.closed, "Conexão não foi fechada corretamente"
    print("[SUCESSO] Teste de conexão e CRUD finalizado com sucesso!")
