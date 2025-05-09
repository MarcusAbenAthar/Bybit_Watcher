import pytest
from plugins.conexao import Conexao


def test_inicializacao_real():
    conexao = Conexao()
    assert conexao.inicializar() is True
    assert conexao.obter_cliente() is not None
    conexao.finalizar()


def test_listar_pares_real():
    conexao = Conexao()
    assert conexao.inicializar() is True
    pares = conexao.listar_pares()
    assert isinstance(pares, list)
    assert len(pares) > 0
    conexao.finalizar()
