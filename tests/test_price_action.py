import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from plugins.price_action import PriceAction


@pytest.fixture
def plugin():
    plugin = PriceAction()
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
    assert plugin.PLUGIN_NAME == "price_action"


def test_executar_com_dados_validos(plugin):
    dados = {"symbol": "BTCUSDT", "timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert isinstance(resultado, dict)
    assert "price_action" in resultado
    assert isinstance(resultado["price_action"], dict)


def test_executar_com_dados_faltantes(plugin):
    # Faltando candles
    dados = {"symbol": "BTCUSDT", "timeframe": "1h"}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert resultado["price_action"] == {}
    # Faltando symbol
    dados = {"timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert resultado["price_action"] == {}
    # Faltando timeframe
    dados = {"symbol": "BTCUSDT", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert resultado["price_action"] == {}
    # dados_completos não é dict
    resultado = plugin.executar(dados_completos=None, symbol="BTCUSDT", timeframe="1h")
    assert resultado["price_action"] == {}


def test_validar_klines(plugin):
    candles = candles_validos()
    assert plugin._validar_klines(candles, "BTCUSDT", "1h") is True
    # Menos de 20 candles
    assert plugin._validar_klines(candles[:5], "BTCUSDT", "1h") is False
    # Candle com valor não numérico
    candles_errado = candles_validos()
    candles_errado[0][1] = "erro"
    assert plugin._validar_klines(candles_errado, "BTCUSDT", "1h") is False
