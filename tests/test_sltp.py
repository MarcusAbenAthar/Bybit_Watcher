import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from plugins.sltp import SLTP


@pytest.fixture
def plugin():
    config = {"sltp_estilos": {"moderado": {"sl_mult": 1.0, "tp_mult": 1.5}}}
    plugin = SLTP()
    plugin.inicializar(config)
    yield plugin
    plugin.finalizar()


def candles_validos():
    # Gera 20 candles OHLCV fake (timestamp, open, high, low, close, volume)
    base = 1710000000000
    candles = []
    for i in range(20):
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
    assert plugin.PLUGIN_NAME == "sltp"


def test_executar_com_dados_validos(plugin):
    dados = {"symbol": "BTCUSDT", "timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert isinstance(resultado, dict)
    assert "sltp" in resultado
    assert isinstance(resultado["sltp"], dict)
    assert "stop_loss" in resultado["sltp"]
    assert "take_profit" in resultado["sltp"]


def test_executar_com_dados_faltantes(plugin):
    # Faltando candles
    dados = {"symbol": "BTCUSDT", "timeframe": "1h"}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert resultado["sltp"]["stop_loss"] is None
    # Faltando symbol
    dados = {"timeframe": "1h", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert resultado["sltp"]["stop_loss"] is None
    # Faltando timeframe
    dados = {"symbol": "BTCUSDT", "crus": candles_validos()}
    resultado = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe=None)
    assert resultado["sltp"]["stop_loss"] is None
    # dados_completos não é dict
    resultado = plugin.executar(dados_completos=None, symbol="BTCUSDT", timeframe="1h")
    assert resultado["sltp"]["stop_loss"] is None
