import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from plugins.analise_candles import AnaliseCandles


@pytest.fixture
def plugin():
    plugin = AnaliseCandles()
    plugin.inicializar({})
    yield plugin
    plugin.finalizar()


def candles_validos():
    # Gera 15 candles OHLCV fake (timestamp, open, high, low, close, volume)
    base = 1710000000000
    candles = []
    for i in range(15):
        ts = base + i * 60000
        o = 100 + i
        h = o + 2
        l = o - 2
        c = o + 1
        v = 10 + i
        candles.append([ts, o, h, l, c, v])
    return candles


def test_inicializacao(plugin):
    assert plugin.inicializado is True
    assert plugin.PLUGIN_NAME == "analise_candles"


def test_executar_com_dados_validos(plugin):
    dados = {"symbol": "BTCUSDT", "timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert isinstance(resultado, dict)
    assert "padroes_candles" in resultado
    assert isinstance(resultado["padroes_candles"], list)


def test_executar_com_dados_faltantes(plugin):
    # Faltando candles
    dados = {"symbol": "BTCUSDT", "timeframe": "1h"}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert resultado == {"padroes_candles": []}
    # Faltando symbol
    dados = {"timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert resultado == {"padroes_candles": []}
    # Faltando timeframe
    dados = {"symbol": "BTCUSDT", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert resultado == {"padroes_candles": []}
    # dados_completos não é dict
    resultado = plugin.executar(dados_completos=None, symbol="BTCUSDT", timeframe="1h")
    assert resultado == {"padroes_candles": []}


def test_validar_candles(plugin):
    candles = candles_validos()
    assert plugin._validar_candles(candles, "BTCUSDT", "1h") is True
    # Menos de 10 candles
    assert plugin._validar_candles(candles[:5], "BTCUSDT", "1h") is False
    # Candle com valor não numérico
    candles_errado = candles_validos()
    candles_errado[0][2] = "erro"
    assert plugin._validar_candles(candles_errado, "BTCUSDT", "1h") is False
