import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from copy import deepcopy
from plugins.analisador_mercado import AnalisadorMercado


@pytest.fixture
def plugin():
    """Fixture que inicializa e finaliza o plugin AnalisadorMercado."""
    plugin = AnalisadorMercado()
    plugin.inicializar({})
    yield plugin
    plugin.finalizar()


@pytest.fixture
def dados_validos():
    """Retorna um dicionário com dados válidos simulados para testes."""
    return {
        "price_action": {
            "direcao": "ALTA",
            "forca": "MÉDIA",
            "confianca": 0.7,
        },
        "medias_moveis": {
            "direcao": "ALTA",
            "forca": "FORTE",
            "confianca": 0.8,
        },
        "tendencia": {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.5,
        },
        "symbol": "BTCUSDT",
        "timeframe": "1h",
    }


def test_inicializacao(plugin):
    """Testa a inicialização do plugin."""
    assert plugin.inicializado is True
    assert plugin.PLUGIN_NAME == "analisador_mercado"
    assert plugin.fontes == ["price_action", "medias_moveis", "tendencia"]
    assert plugin.MINIMO_FONTES == 2


def test_inicializacao_com_config_invalida():
    """Testa a inicialização com configuração inválida."""
    plugin = AnalisadorMercado()
    assert plugin.inicializar(None) is False
    assert plugin.inicializado is False


def test_executar_com_dados_validos(plugin, dados_validos):
    """Testa a execução com dados válidos."""
    dados = deepcopy(dados_validos)
    result = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert result is True
    assert "analise_mercado" in dados
    assert dados["analise_mercado"]["direcao"] == "ALTA"
    assert dados["analise_mercado"]["forca"] == "MÉDIA"  # 2 confirmações
    assert isinstance(dados["analise_mercado"]["confianca"], float)
    assert 0.0 <= dados["analise_mercado"]["confianca"] <= 1.0


def test_executar_com_dados_faltantes(plugin):
    """Testa a execução com parâmetros ausentes."""
    dados = {}
    result = plugin.executar(dados_completos=dados, symbol=None, timeframe="1h")
    assert result is True
    assert dados["analise_mercado"]["direcao"] == "LATERAL"
    assert dados["analise_mercado"]["forca"] == "FRACA"
    assert dados["analise_mercado"]["confianca"] == 0.0


def test_executar_com_dados_completos_none(plugin):
    """Testa a execução com dados_completos=None."""
    result = plugin.executar(dados_completos=None, symbol="BTCUSDT", timeframe="1h")
    assert result is True  # Não deve modificar None, apenas retornar True


def test_executar_com_fontes_insuficientes(plugin, dados_validos):
    """Testa a execução com menos fontes do que o mínimo exigido."""
    dados = deepcopy(dados_validos)
    # Remove duas fontes, deixando apenas uma
    dados.pop("price_action")
    dados.pop("medias_moveis")
    result = plugin.executar(dados_completos=dados, symbol="BTCUSDT", timeframe="1h")
    assert result is True
    assert dados["analise_mercado"]["direcao"] == "LATERAL"
    assert dados["analise_mercado"]["forca"] == "FRACA"
    assert dados["analise_mercado"]["confianca"] == 0.0


def test_validar_resultado_fonte(plugin):
    """Testa a validação de resultados de fontes."""
    # Resultado válido
    resultado = {
        "direcao": "ALTA",
        "forca": "FORTE",
        "confianca": 0.9,
    }
    validated = plugin._validar_resultado_fonte(resultado, "price_action")
    assert validated == resultado

    # Resultado com valores inválidos
    resultado_invalido = {
        "direcao": "INVALIDO",
        "forca": "ERRADO",
        "confianca": "NÃO_NUMÉRICO",
    }
    validated = plugin._validar_resultado_fonte(resultado_invalido, "price_action")
    assert validated == {
        "direcao": "LATERAL",
        "forca": "FRACA",
        "confianca": 0.0,
    }

    # Resultado não é dicionário
    validated = plugin._validar_resultado_fonte("invalido", "price_action")
    assert validated == {
        "direcao": "LATERAL",
        "forca": "FRACA",
        "confianca": 0.0,
    }


def test_coletar_resultados(plugin, dados_validos):
    """Testa a coleta de resultados das fontes."""
    dados = deepcopy(dados_validos)
    resultados = plugin._coletar_resultados(dados)
    assert len(resultados) == 3
    assert "price_action" in resultados
    assert "medias_moveis" in resultados
    assert "tendencia" in resultados
    assert resultados["price_action"]["direcao"] == "ALTA"
    assert resultados["medias_moveis"]["confianca"] == 0.8


def test_coletar_resultados_com_fonte_ausente(plugin, dados_validos):
    """Testa a coleta de resultados com uma fonte ausente."""
    dados = deepcopy(dados_validos)
    dados.pop("price_action")  # Remove uma fonte
    resultados = plugin._coletar_resultados(dados)
    assert len(resultados) == 2
    assert "price_action" not in resultados
    assert "medias_moveis" in resultados
    assert "tendencia" in resultados


def test_consolidar_resultados(plugin):
    """Testa a consolidação de resultados."""
    resultados = {
        "price_action": {
            "direcao": "ALTA",
            "forca": "MÉDIA",
            "confianca": 0.7,
        },
        "medias_moveis": {
            "direcao": "ALTA",
            "forca": "FORTE",
            "confianca": 0.8,
        },
        "tendencia": {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.5,
        },
    }
    consolidado = plugin._consolidar_resultados(resultados)
    assert consolidado["direcao"] == "ALTA"
    assert consolidado["forca"] == "MÉDIA"  # 2 confirmações
    assert consolidado["confianca"] == pytest.approx(0.5, abs=0.1)  # (0.7+0.8)/2 * 2/3


def test_consolidar_resultados_todos_lateral(plugin):
    """Testa a consolidação quando todas as direções são LATERAL."""
    resultados = {
        "price_action": {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.5,
        },
        "medias_moveis": {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.6,
        },
    }
    consolidado = plugin._consolidar_resultados(resultados)
    assert consolidado["direcao"] == "LATERAL"
    assert consolidado["forca"] == "FRACA"
    assert consolidado["confianca"] == 0.0
