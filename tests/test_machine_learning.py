import pytest
from plugins.machine_learning import MachineLearning
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
def plugin_ml():
    return MachineLearning()


@pytest.mark.skip(reason="Teste de ML pulado conforme solicitado pelo usuário.")
def test_machine_learning_real(plugin_ml, candles_reais):
    dados = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "crus": candles_reais,
    }
    resultado = plugin_ml.executar(dados_completos=dados)
    assert isinstance(resultado, dict)
    assert any(
        k in resultado for k in ["previsao", "analise", "resultado", "machine_learning"]
    )
