import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from plugins.calculo_alavancagem import CalculoAlavancagem


@pytest.fixture
def plugin():
    plugin = CalculoAlavancagem()
    plugin.inicializar({})
    yield plugin
    plugin.finalizar()


def klines_validos():
    # Gera 20 klines OHLCV fake (timestamp, open, high, low, close, volume)
    base = 1710000000000
    klines = []
    for i in range(20):
        ts = base + i * 60000
        o = 100 + i
        h = o + 2
        l = o - 2
        c = o + 1
        v = 1000 + i
        klines.append([ts, o, h, l, c, v])
    return klines


def test_inicializacao(plugin):
    assert plugin.inicializado is True
    assert plugin.PLUGIN_NAME == "calculo_alavancagem"


def test_executar_com_dados_validos(plugin):
    dados = {"symbol": "BTCUSDT", "timeframe": "1h", "crus": klines_validos()}
    resultado = plugin.executar(
        dados_completos=dados,
        symbol="BTCUSDT",
        timeframe="1h",
        direcao="ALTA",
        confianca=0.8,
    )
    assert isinstance(resultado, dict)
    assert "alavancagem" in resultado
    assert isinstance(resultado["alavancagem"], (int, float))


def test_executar_com_dados_faltantes(plugin):
    # Faltando klines
    dados = {"symbol": "BTCUSDT", "timeframe": "1h"}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert resultado["alavancagem"] == plugin._alav_min
    # Faltando symbol
    dados = {"timeframe": "1h", "crus": klines_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert resultado["alavancagem"] == plugin._alav_min
    # Faltando timeframe
    dados = {"symbol": "BTCUSDT", "crus": klines_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert resultado["alavancagem"] == plugin._alav_min
    # dados_completos não é dict
    resultado = plugin.executar(dados_completos=None, symbol="BTCUSDT", timeframe="1h")
    assert resultado["alavancagem"] == plugin._alav_min


def test_validar_klines(plugin):
    klines = klines_validos()
    assert plugin._validar_klines(klines, "BTCUSDT", "1h") is True
    # Menos de 14 klines
    assert plugin._validar_klines(klines[:5], "BTCUSDT", "1h") is False
    # Kline com valor não numérico
    klines_errado = klines_validos()
    klines_errado[0][2] = "erro"
    assert plugin._validar_klines(klines_errado, "BTCUSDT", "1h") is False
