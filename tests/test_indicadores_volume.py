import pytest
from plugins.indicadores.indicadores_volume import IndicadoresVolume
from plugins.obter_dados import ObterDados
from plugins.conexao import Conexao


@pytest.fixture(scope="module")
def conexao_real():
    conexao = Conexao()
    assert conexao.inicializar() is True
    yield conexao
    conexao.finalizar()


@pytest.fixture
def candles_reais(conexao_real):
    plugin = ObterDados(conexao=conexao_real)
    dados = {}
    symbol = "BTCUSDT"
    timeframe = "1h"
    plugin.executar(dados, symbol, timeframe, limit=20)
    return dados["crus"]


@pytest.fixture
def plugin_volume():
    return IndicadoresVolume()


def test_indicadores_volume_real(plugin_volume, candles_reais):
    dados = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "crus": candles_reais,
    }
    resultado = plugin_volume.executar(
        dados_completos=dados, symbol="BTCUSDT", timeframe="1h"
    )
    assert isinstance(resultado, dict)
    assert "volume" in resultado
    assert isinstance(resultado["volume"], dict)
