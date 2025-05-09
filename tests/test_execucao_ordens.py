import pytest
from plugins.execucao_ordens import ExecucaoOrdens
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
def plugin_execucao():
    config = {
        "trading": {
            "auto_trade": True,
            "risco_por_operacao": 0.01,
            "dca_percentual": 0.1,
        }
    }
    plugin = ExecucaoOrdens()
    plugin._config = config
    return plugin


def test_simular_execucao_ordem(plugin_execucao, candles_reais):
    dados = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "crus": candles_reais,
        "direcao": "LONG",
        "preco_atual": candles_reais[-1][4],
        "alavancagem": 5,
        "stop_loss": candles_reais[-1][4] * 0.98,
        "take_profit": candles_reais[-1][4] * 1.02,
    }
    # Simula execução (não envia ordem real)
    resultado = plugin_execucao.executar(
        dados_completos=dados, symbol="BTCUSDT", timeframe="1h", simular=True
    )
    assert isinstance(resultado, dict)
    assert (
        "quantidade" in resultado
        or "params" in resultado
        or "status" in resultado
        or "resultado" in resultado
    )
