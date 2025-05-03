import pytest
from unittest.mock import MagicMock, patch
from plugins.banco_dados import BancoDados


@pytest.fixture
def gerenciador_banco_mock():
    mock = MagicMock()
    mock.inicializado = True
    mock.conn = MagicMock()
    return mock


@pytest.fixture
def plugin(gerenciador_banco_mock):
    plugin = BancoDados(gerenciador_banco=gerenciador_banco_mock)
    return plugin


def test_plugin_properties(plugin):
    assert plugin.PLUGIN_NAME == "banco_dados"
    assert plugin.PLUGIN_CATEGORIA == "plugin"
    assert isinstance(plugin.PLUGIN_TAGS, list)
    assert plugin.plugin_schema_versao == "1.0"
    assert isinstance(plugin.plugin_tabelas, dict)
    assert "dados" in plugin.plugin_tabelas


def test_dependencias():
    assert "gerenciador_banco" in BancoDados.dependencias()


def test_inicializar_sucesso(plugin, gerenciador_banco_mock):
    # Simula cursor válido
    cursor_mock = MagicMock()
    gerenciador_banco_mock.conn.cursor.return_value = cursor_mock
    assert plugin.inicializar({}) is True
    assert plugin.inicializado is True
    assert plugin._cursor is cursor_mock


def test_inicializar_falha_sem_gerenciador():
    plugin = BancoDados(gerenciador_banco=None)
    assert plugin.inicializar({}) is False


def test_inicializar_falha_sem_conexao(gerenciador_banco_mock):
    gerenciador_banco_mock.conn = None
    plugin = BancoDados(gerenciador_banco=gerenciador_banco_mock)
    assert plugin.inicializar({}) is False


def test_finalizar(plugin, gerenciador_banco_mock):
    cursor_mock = MagicMock()
    gerenciador_banco_mock.conn.cursor.return_value = cursor_mock
    plugin.inicializar({})
    plugin.finalizar()
    assert plugin.inicializado is False
    cursor_mock.close.assert_called()


def test_registrar_tabela(plugin):
    plugin._cursor = MagicMock()
    plugin._conn = MagicMock()
    plugin.registrar_tabela("banco_dados", "dados")
    assert "banco_dados" in plugin._tabelas_registradas
    assert "dados" in plugin._tabelas_registradas["banco_dados"]


def test_get_tabelas_por_plugin(plugin):
    plugin._tabelas_registradas = {"banco_dados": ["dados"]}
    tabelas = plugin.get_tabelas_por_plugin()
    assert tabelas == {"banco_dados": ["dados"]}


@pytest.mark.parametrize(
    "dados, esperado",
    [
        (
            {
                "timestamp": "2024-01-01 00:00:00",
                "symbol": "BTCUSDT",
                "valor": 123.45,
                "tipo": "teste",
                "plugin_origem": "banco_dados",
            },
            True,
        ),
        ({}, False),
    ],
)
def test_inserir(plugin, dados, esperado):
    plugin._cursor = MagicMock()
    plugin._conn = MagicMock()
    plugin._cursor.fetchone.return_value = [1]

    resultado = plugin.inserir("dados", dados)

    assert resultado is esperado
    if esperado:
        plugin._cursor.execute.assert_called()
        plugin._conn.commit.assert_called()
    else:
        plugin._cursor.execute.assert_not_called()


def test_inserir_klines(plugin):
    plugin._cursor = MagicMock()
    plugin._conn = MagicMock()
    plugin._cursor.fetchone.return_value = [1]
    kline = [
        1704067200000,  # timestamp
        42000.0,  # open
        42100.0,  # high
        41900.0,  # low
        42050.0,  # close
        10.0,  # volume
        1704067260000,  # close_time
        420500.0,  # quote_volume
        100,  # trades
        5.0,  # taker_buy_base
        210250.0,  # taker_buy_quote
    ]
    assert plugin.inserir_klines([kline], "BTCUSDT", "1m") is True


@pytest.mark.parametrize(
    "cursor_value, esperado",
    [
        (None, []),
        (
            [(1, "2024-01-01 00:00:00", "BTCUSDT", 123.45, "teste", "banco_dados")],
            [
                {
                    "id": 1,
                    "timestamp": "2024-01-01 00:00:00",
                    "symbol": "BTCUSDT",
                    "valor": 123.45,
                    "tipo": "teste",
                    "plugin_origem": "banco_dados",
                }
            ],
        ),
    ],
)
def test_buscar(plugin, cursor_value, esperado):
    plugin._cursor = MagicMock()
    plugin._cursor.fetchall.return_value = cursor_value
    plugin._cursor.description = [
        ("id",),
        ("timestamp",),
        ("symbol",),
        ("valor",),
        ("tipo",),
        ("plugin_origem",),
    ]
    resultado = plugin.buscar("dados")
    assert resultado == esperado
