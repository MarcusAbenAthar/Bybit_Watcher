import pytest
from plugins.obter_dados import ObterDados
from plugins.conexao import Conexao


@pytest.fixture(scope="module")
def conexao_real():
    conexao = Conexao()
    assert conexao.inicializar() is True
    yield conexao
    conexao.finalizar()


@pytest.fixture
def plugin_obter_dados(conexao_real):
    return ObterDados(conexao=conexao_real)


def test_obter_candles_reais(plugin_obter_dados):
    dados = {}
    symbol = "BTCUSDT"
    timeframe = "1h"
    ok = plugin_obter_dados.executar(dados, symbol, timeframe, limit=10)
    assert ok is True
    assert "crus" in dados
    assert isinstance(dados["crus"], list)
    assert len(dados["crus"]) > 0
    for candle in dados["crus"]:
        assert isinstance(candle, list)
        assert len(candle) >= 5
        assert all(isinstance(x, (int, float)) for x in candle[:5])
