import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from plugins.validador_dados import ValidadorDados


@pytest.fixture
def plugin():
    plugin = ValidadorDados()
    plugin.inicializar({})
    yield plugin
    plugin.finalizar()


def candles_validos():
    # Gera 25 candles OHLCV fake (timestamp, open, high, low, close, volume)
    base = 1710000000000
    candles = []
    for i in range(25):
        ts = base + i * 60000
        o = 100 + i
        h = o + 2
        l = o - 2
        c = o + 1
        v = 1000 + i
        candles.append([ts, o, h, l, c, v])
    return candles


def test_inicializacao(plugin):
    assert plugin.inicializado is True
    assert plugin.PLUGIN_NAME == "validador_dados"


def test_executar_com_dados_validos(plugin):
    dados = {"symbol": "BTCUSDT", "timeframe": "1h", "crus": candles_validos()}
    plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert "validador_dados" in dados
    assert dados["validador_dados"]["status"] == "VALIDO"


def test_executar_com_dados_faltantes(plugin):
    # Faltando candles
    dados = {"symbol": "BTCUSDT", "timeframe": "1h"}
    plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert dados["validador_dados"]["status"] == "INVALIDO"
    # Faltando symbol
    dados = {"timeframe": "1h", "crus": candles_validos()}
    plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert dados["validador_dados"]["status"] == "INVALIDO"
    # Faltando timeframe
    dados = {"symbol": "BTCUSDT", "crus": candles_validos()}
    plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert dados["validador_dados"]["status"] == "INVALIDO"
    # dados_completos não é dict
    dados = None
    result = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert result is True  # Verifica que o método retorna True
    assert dados is None  # Verifica que dados permanece None


def test_validar(plugin):
    candles = candles_validos()
    assert plugin._validar(candles, "BTCUSDT", "1h") is True
    # Menos de 20 candles
    assert plugin._validar(candles[:5], "BTCUSDT", "1h") is False
    # Candle com valor não numérico
    candles_errado = candles_validos()
    candles_errado[0][1] = "erro"
    assert plugin._validar(candles_errado, "BTCUSDT", "1h") is False
