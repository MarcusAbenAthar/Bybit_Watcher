import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from plugins.indicadores.indicadores_tendencia import IndicadoresTendencia


class DummyGerente:
    pass


@pytest.fixture
def plugin():
    plugin = IndicadoresTendencia(gerente=DummyGerente())
    plugin.inicializar({})
    yield plugin
    plugin.finalizar()


def candles_validos():
    # Gera 40 candles OHLCV fake (timestamp, open, high, low, close, volume)
    base = 1710000000000
    candles = []
    for i in range(40):
        ts = base + i * 60000
        o = 100 + i
        h = o + 2
        l = o - 2
        c = o + 1
        v = 1000 + i
        candles.append([ts, o, h, l, c, v])
    return candles


def test_inicializacao(plugin):
    assert plugin.PLUGIN_NAME == "indicadores_tendencia"


def test_executar_com_dados_validos(plugin):
    dados = {"crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert isinstance(resultado, dict) or resultado is None


def test_executar_com_dados_faltantes(plugin):
    # Faltando candles
    dados = {}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert resultado is None or isinstance(resultado, dict)
    # Faltando symbol
    dados = {"crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert resultado is None or isinstance(resultado, dict)
    # Faltando timeframe
    dados = {"crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert resultado is None or isinstance(resultado, dict)
