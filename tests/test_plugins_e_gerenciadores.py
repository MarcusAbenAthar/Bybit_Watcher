"""
DICA: Para visualizar os prints deste teste no console, execute:
    pytest -s tests/test_plugins_e_gerenciadores.py -v
Assim, todas as etapas de inicialização, integração e finalização serão mostradas no terminal.
"""
import pytest
from utils.config import carregar_config

# Gerenciadores
from plugins.gerenciadores.gerenciador_banco import GerenciadorBanco
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins

# Plugins principais
from plugins.banco_dados import BancoDados
from plugins.conexao import Conexao
from plugins.analise_candles import AnaliseCandles
from plugins.analisador_mercado import AnalisadorMercado
from plugins.calculo_alavancagem import CalculoAlavancagem
from plugins.calculo_risco import CalculoRisco
from plugins.execucao_ordens import ExecucaoOrdens
from plugins.medias_moveis import MediasMoveis
from plugins.obter_dados import ObterDados
from plugins.plugin import Plugin
from plugins.price_action import PriceAction
from plugins.sinais_plugin import SinaisPlugin
from plugins.sltp import SLTP
from plugins.validador_dados import ValidadorDados

# Plugins de indicadores
from plugins.indicadores.indicadores_osciladores import IndicadoresOsciladores
from plugins.indicadores.indicadores_tendencia import IndicadoresTendencia
from plugins.indicadores.indicadores_volatilidade import IndicadoresVolatilidade
from plugins.indicadores.indicadores_volume import IndicadoresVolume
from plugins.indicadores.outros_indicadores import OutrosIndicadores

@pytest.fixture(scope="module")
def config():
    print("[FIXTURE] Carregando configuração global do sistema...")
    return carregar_config()

# Gerenciadores

def test_gerenciador_banco_init(config):
    print("[TESTE] Inicializando GerenciadorBanco...")
    gb = GerenciadorBanco()
    assert gb.inicializar(config), "Falha ao inicializar GerenciadorBanco"
    print("[OK] GerenciadorBanco inicializado!")
    gb.finalizar()
    print("[OK] GerenciadorBanco finalizado.")

def test_gerenciador_bot_init(config):
    print("[TESTE] Inicializando GerenciadorBot...")
    gb = GerenciadorBot()
    assert gb.inicializar(config), "Falha ao inicializar GerenciadorBot"
    print("[OK] GerenciadorBot inicializado!")
    gb.finalizar()
    print("[OK] GerenciadorBot finalizado.")

def test_gerenciador_plugins_init(config):
    print("[TESTE] Inicializando GerenciadorPlugins...")
    gp = GerenciadorPlugins()
    assert gp.inicializar(config), "Falha ao inicializar GerenciadorPlugins"
    print("[OK] GerenciadorPlugins inicializado!")
    gp.finalizar()
    print("[OK] GerenciadorPlugins finalizado.")

# Plugins principais

def test_plugin_banco_dados_init(config):
    print("[TESTE] Inicializando BancoDados (com GerenciadorBanco)...")
    gb = GerenciadorBanco()
    assert gb.inicializar(config), "Falha ao inicializar GerenciadorBanco"
    bd = BancoDados(gerenciador_banco=gb)
    assert bd.inicializar(config), "Falha ao inicializar BancoDados"
    print("[OK] BancoDados inicializado!")
    bd.finalizar()
    gb.finalizar()
    print("[OK] BancoDados e GerenciadorBanco finalizados.")

def test_plugin_conexao_init(config):
    print("[TESTE] Inicializando plugin Conexao...")
    conexao = Conexao()
    assert conexao.inicializar(config), "Falha ao inicializar plugin Conexao"
    print("[OK] Plugin Conexao inicializado!")
    conexao.finalizar()
    print("[OK] Plugin Conexao finalizado.")

def test_plugin_analise_candles_init(config):
    print("[TESTE] Inicializando plugin AnaliseCandles...")
    plugin = AnaliseCandles()
    assert plugin.inicializar(config), "Falha ao inicializar AnaliseCandles"
    print("[OK] AnaliseCandles inicializado!")
    plugin.finalizar()
    print("[OK] AnaliseCandles finalizado.")

def test_plugin_analisador_mercado_init(config):
    print("[TESTE] Inicializando plugin AnalisadorMercado...")
    plugin = AnalisadorMercado()
    assert plugin.inicializar(config), "Falha ao inicializar AnalisadorMercado"
    print("[OK] AnalisadorMercado inicializado!")
    plugin.finalizar()
    print("[OK] AnalisadorMercado finalizado.")

def test_plugin_calculo_alavancagem_init(config):
    print("[TESTE] Inicializando plugin CalculoAlavancagem...")
    plugin = CalculoAlavancagem()
    assert plugin.inicializar(config), "Falha ao inicializar CalculoAlavancagem"
    print("[OK] CalculoAlavancagem inicializado!")
    plugin.finalizar()
    print("[OK] CalculoAlavancagem finalizado.")

def test_plugin_calculo_risco_init(config):
    print("[TESTE] Inicializando plugin CalculoRisco...")
    plugin = CalculoRisco()
    assert plugin.inicializar(config), "Falha ao inicializar CalculoRisco"
    print("[OK] CalculoRisco inicializado!")
    plugin.finalizar()
    print("[OK] CalculoRisco finalizado.")

def test_plugin_execucao_ordens_init(config):
    print("[TESTE] Inicializando plugin ExecucaoOrdens (com Conexao)...")
    conexao = Conexao()
    assert conexao.inicializar(config), "Falha ao inicializar Conexao"
    plugin = ExecucaoOrdens(conexao=conexao)
    assert plugin.inicializar(config), "Falha ao inicializar ExecucaoOrdens"
    print("[OK] ExecucaoOrdens inicializado!")
    plugin.finalizar()
    conexao.finalizar()
    print("[OK] ExecucaoOrdens e Conexao finalizados.")

def test_plugin_medias_moveis_init(config):
    print("[TESTE] Inicializando plugin MediasMoveis...")
    plugin = MediasMoveis()
    assert plugin.inicializar(config), "Falha ao inicializar MediasMoveis"
    print("[OK] MediasMoveis inicializado!")
    plugin.finalizar()
    print("[OK] MediasMoveis finalizado.")

def test_plugin_obter_dados_init(config):
    print("[TESTE] Inicializando plugin ObterDados (com Conexao)...")
    conexao = Conexao()
    assert conexao.inicializar(config), "Falha ao inicializar Conexao"
    plugin = ObterDados(conexao=conexao)
    assert plugin.inicializar(config), "Falha ao inicializar ObterDados"
    print("[OK] ObterDados inicializado!")
    plugin.finalizar()
    conexao.finalizar()
    print("[OK] ObterDados e Conexao finalizados.")

def test_plugin_price_action_init(config):
    print("[TESTE] Inicializando plugin PriceAction...")
    plugin = PriceAction()
    assert plugin.inicializar(config), "Falha ao inicializar PriceAction"
    print("[OK] PriceAction inicializado!")
    plugin.finalizar()
    print("[OK] PriceAction finalizado.")

def test_plugin_sinais_plugin_init(config):
    print("[TESTE] Inicializando plugin SinaisPlugin...")
    plugin = SinaisPlugin()
    assert plugin.inicializar(config), "Falha ao inicializar SinaisPlugin"
    print("[OK] SinaisPlugin inicializado!")
    plugin.finalizar()
    print("[OK] SinaisPlugin finalizado.")

def test_plugin_sltp_init(config):
    print("[TESTE] Inicializando plugin SLTP...")
    plugin = SLTP()
    assert plugin.inicializar(config), "Falha ao inicializar SLTP"
    print("[OK] SLTP inicializado!")
    plugin.finalizar()
    print("[OK] SLTP finalizado.")

def test_plugin_validador_dados_init(config):
    print("[TESTE] Inicializando plugin ValidadorDados...")
    plugin = ValidadorDados()
    assert plugin.inicializar(config), "Falha ao inicializar ValidadorDados"
    print("[OK] ValidadorDados inicializado!")
    plugin.finalizar()
    print("[OK] ValidadorDados finalizado.")

# Indicadores

def test_indicadores_osciladores_init(config):
    print("[TESTE] Inicializando plugin IndicadoresOsciladores (com GerenciadorBot)...")
    gerente = GerenciadorBot()
    assert gerente.inicializar(config), "Falha ao inicializar GerenciadorBot"
    plugin = IndicadoresOsciladores(gerente=gerente)
    assert plugin.inicializar(config), "Falha ao inicializar IndicadoresOsciladores"
    print("[OK] IndicadoresOsciladores inicializado!")
    plugin.finalizar()
    gerente.finalizar()
    print("[OK] IndicadoresOsciladores e GerenciadorBot finalizados.")

def test_indicadores_tendencia_init(config):
    print("[TESTE] Inicializando plugin IndicadoresTendencia (com GerenciadorBot)...")
    gerente = GerenciadorBot()
    assert gerente.inicializar(config), "Falha ao inicializar GerenciadorBot"
    plugin = IndicadoresTendencia(gerente=gerente)
    assert plugin.inicializar(config), "Falha ao inicializar IndicadoresTendencia"
    print("[OK] IndicadoresTendencia inicializado!")
    plugin.finalizar()
    gerente.finalizar()
    print("[OK] IndicadoresTendencia e GerenciadorBot finalizados.")

def test_indicadores_volatilidade_init(config):
    print("[TESTE] Inicializando plugin IndicadoresVolatilidade...")
    plugin = IndicadoresVolatilidade()
    assert plugin.inicializar(config), "Falha ao inicializar IndicadoresVolatilidade"
    print("[OK] IndicadoresVolatilidade inicializado!")
    plugin.finalizar()
    print("[OK] IndicadoresVolatilidade finalizado.")

def test_indicadores_volume_init(config):
    print("[TESTE] Inicializando plugin IndicadoresVolume (com GerenciadorBot)...")
    gerente = GerenciadorBot()
    assert gerente.inicializar(config), "Falha ao inicializar GerenciadorBot"
    plugin = IndicadoresVolume(gerente=gerente)
    assert plugin.inicializar(config), "Falha ao inicializar IndicadoresVolume"
    print("[OK] IndicadoresVolume inicializado!")
    plugin.finalizar()
    gerente.finalizar()
    print("[OK] IndicadoresVolume e GerenciadorBot finalizados.")

def test_outros_indicadores_init(config):
    print("[TESTE] Inicializando plugin OutrosIndicadores (com GerenciadorBot)...")
    gerente = GerenciadorBot()
    assert gerente.inicializar(config), "Falha ao inicializar GerenciadorBot"
    plugin = OutrosIndicadores(gerente=gerente)
    assert plugin.inicializar(config), "Falha ao inicializar OutrosIndicadores"
    print("[OK] OutrosIndicadores inicializado!")
    plugin.finalizar()
    gerente.finalizar()
    print("[OK] OutrosIndicadores e GerenciadorBot finalizados.")

# Testes cruzados de dependências (exemplo)
def test_banco_dados_e_conexao_cruzado(config):
    print("[TESTE] Inicializando BancoDados (com GerenciadorBanco) e Conexao juntos...")
    gb = GerenciadorBanco()
    assert gb.inicializar(config), "Falha ao inicializar GerenciadorBanco"
    bd = BancoDados(gerenciador_banco=gb)
    assert bd.inicializar(config), "Falha ao inicializar BancoDados"
    conexao = Conexao()
    assert conexao.inicializar(config), "Falha ao inicializar Conexao"
    print("[OK] BancoDados, GerenciadorBanco e Conexao inicializados juntos!")
    conexao.finalizar()
    bd.finalizar()
    gb.finalizar()
    print("[OK] Todos os componentes finalizados com segurança.")
