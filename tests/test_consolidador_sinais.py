import pytest
from plugins.consolidador_sinais import ConsolidadorSinais
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
def plugin_consolidador():
    return ConsolidadorSinais()


def test_consolidar_sinal_real(plugin_consolidador, candles_reais):
    dados = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "crus": candles_reais,
        "analise_mercado": {
            "direcao": "ALTA",
            "forca": "MÉDIA",
            "confianca": 0.7,
            "preco_atual": candles_reais[-1][4],
            "volume": 1000,
            "rsi": 50,
            "tendencia": "ALTA",
            "suporte": 0,
            "resistencia": 0,
            "atr": 1000,
            "stop_loss": candles_reais[-1][4] * 0.98,
            "take_profit": candles_reais[-1][4] * 1.02,
            "alavancagem": 5,
        },
    }
    resultado = plugin_consolidador.executar(dados_completos=dados)
    assert "sinal_consolidado" in resultado
    sinal = resultado["sinal_consolidado"]
    assert sinal["symbol"] == "BTCUSDT"
    assert sinal["preco_atual"] == candles_reais[-1][4]
    assert sinal["alavancagem"] == 5
    assert sinal["stop_loss"] > 0
    assert sinal["take_profit"] > 0
