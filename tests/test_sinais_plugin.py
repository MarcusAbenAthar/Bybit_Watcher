import pytest
from plugins.sinais_plugin import SinaisPlugin
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
def plugin_sinais():
    return SinaisPlugin()


def test_gerar_sinal_real(plugin_sinais, candles_reais):
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
        },
    }
    resultado = plugin_sinais.executar(
        symbol="BTCUSDT", timeframe="1h", dados_completos=dados
    )
    assert isinstance(resultado, dict)
    assert "analise_mercado" in resultado or "sinal" in resultado
    analise = resultado.get("analise_mercado") or resultado.get("sinal")
    assert analise["direcao"] in ["ALTA", "BAIXA", "LATERAL", "LONG", "SHORT"]
    assert analise["preco_atual"] == candles_reais[-1][4]
    assert analise["confianca"] is not None
