import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from plugins.indicadores.indicadores_volatilidade import IndicadoresVolatilidade


@pytest.fixture
def plugin():
    plugin = IndicadoresVolatilidade()
    plugin.inicializar({})
    yield plugin
    plugin.finalizar()


def candles_validos():
    # Gera 30 candles OHLCV fake (timestamp, open, high, low, close, volume)
    base = 1710000000000
    candles = []
    for i in range(30):
        ts = base + i * 60000
        o = 100 + i
        h = o + 2
        l = o - 2
        c = o + 1
        v = 1000 + i
        candles.append([ts, o, h, l, c, v])
    return candles


def test_inicializacao(plugin):
    assert plugin.PLUGIN_NAME == "indicadores_volatilidade"


def test_executar_com_dados_validos(plugin):
    dados = {"symbol": "BTCUSDT", "timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert isinstance(resultado, dict)
    assert "volatilidade" in resultado
    assert isinstance(resultado["volatilidade"], dict)


def test_executar_com_dados_faltantes(plugin):
    # Faltando candles
    dados = {"symbol": "BTCUSDT", "timeframe": "1h"}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert resultado["volatilidade"]["atr"] is None
    # Faltando symbol
    dados = {"timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert resultado["volatilidade"]["atr"] is None
    # Faltando timeframe
    dados = {"symbol": "BTCUSDT", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert resultado["volatilidade"]["atr"] is None
    # dados_completos não é dict
    resultado = plugin.executar(dados_completos=None, symbol="BTCUSDT", timeframe="1h")
    assert resultado["volatilidade"]["atr"] is None
