"""
Bot de análise de mercado cripto seguindo as Regras de Ouro.

Author: Marcus Aben-Athar
Date: 2025-02-08
Repository: https://github.com/MarcusAbenAthar/Bybit_Watcher

Regras de Ouro implementadas:
1. Autonomo - Análise e decisões automáticas
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros e logs
4. Certeiro - Alta precisão nas análises
5. Eficiente - Otimizado e rápido
6. Clareza - Código limpo e legível
7. Modular - Arquitetura em plugins
8. Plugins - Sistema extensível
9. Testável - 100% cobertura
10. Documentado - Docstrings completas
"""

# Imports stdlib
import logging
import signal
import sys
from typing import Optional
import time

# Imports terceiros
from dotenv import load_dotenv
import os

# Imports locais
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.config import carregar_config
from utils.handlers import signal_handler
from utils.logging_config import configurar_logging

# Configuração inicial
load_dotenv()
logger = logging.getLogger(__name__)

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

# Plugins essenciais em ordem de dependência
PLUGINS_ESSENCIAIS = [
    "conexao",  # Sem dependências
    "gerenciadores/gerenciador_banco",  # Sem dependências
    "banco_dados",  # Depende de gerenciador_banco
    "validador_dados",  # Base para outros plugins
    "calculo_alavancagem",  # Base para indicadores_tendencia
    "indicadores.indicadores_tendencia",  # Necessário para sinais
    "medias_moveis",  # Necessário para sinais
    "sinais_plugin",  # Depende dos indicadores
    "gerenciadores/gerenciador_bot",  # Depende de banco_dados e gerenciador_banco
]

# Plugins adicionais em ordem de dependência
PLUGINS_ADICIONAIS = [
    "price_action",  # Análise técnica
    "analise_candles",  # Análise técnica
    "calculo_risco",
    "execucao_ordens",
    "indicadores.indicadores_osciladores",
    "indicadores.indicadores_volatilidade",
    "indicadores.indicadores_volume",
    "indicadores.outros_indicadores",
]


def inicializar_bot() -> GerentePlugin:
    """
    Inicializa o bot de forma segura.

    Returns:
        GerentePlugin: Gerenciador inicializado

    Raises:
        RuntimeError: Se falhar a inicialização
    """
    try:
        # Carrega config
        config = carregar_config()

        # Inicializa o gerente
        gerente = GerentePlugin()
        gerente.inicializar(config)

        # Carrega plugins essenciais na ordem de dependência
        for plugin_name in PLUGINS_ESSENCIAIS:
            if not gerente.carregar_plugin(plugin_name):
                raise RuntimeError(f"Falha ao carregar plugin essencial: {plugin_name}")

        # Validação final
        if not gerente.verificar_plugins_essenciais():
            raise RuntimeError("Plugins essenciais não inicializados")

        return gerente

    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        raise RuntimeError(f"Falha ao inicializar bot: {e}")


def main() -> None:
    """Função principal do bot."""
    try:
        # Setup inicial
        configurar_logging()  # Initialize logging
        logger.info("Iniciando bot...")
        signal.signal(signal.SIGINT, signal_handler)

        # Inicialização do gerente de plugins
        gerente_plugin = inicializar_bot()

        # Carregar plugins adicionais antes de iniciar o bot
        for plugin_name in PLUGINS_ADICIONAIS:
            if not gerente_plugin.carregar_plugin(plugin_name):
                logger.warning(f"Falha ao carregar plugin adicional: {plugin_name}")

        # Inicialização do gerenciador do bot
        gerenciador_bot = GerenciadorBot()
        gerenciador_bot.gerente = (
            gerente_plugin  # Injeta o gerente com plugins registrados
        )

        if not gerenciador_bot.inicializar(gerente_plugin.config):
            raise RuntimeError("Falha ao inicializar gerenciador do bot")

        # Registra todos os plugins carregados do gerente no GerenciadorBot
        for nome, plugin in gerente_plugin.plugins.items():
            if not gerenciador_bot.registrar_plugin(plugin):
                logger.error(f"Falha ao registrar plugin {nome}")
                raise RuntimeError(f"Falha ao registrar plugin {nome}")

        # Inicia o bot
        if not gerenciador_bot.iniciar():
            raise RuntimeError("Falha ao iniciar gerenciador do bot")
        logger.info("Bot iniciado com sucesso")

        # Carrega os timeframes do config
        config = gerente_plugin.config
        timeframes = config.get(
            "timeframes", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        )  # Default caso não esteja no config
        par = "BTCUSDT"

        # Loop principal
        while True:
            try:
                logger.debug("Iniciando ciclo de execução...")
                resultados = gerenciador_bot.executar_ciclo(par="BTCUSDT")
                if not resultados:
                    logger.warning("Falha no ciclo do gerenciador do bot")
                    break
                logger.debug("Ciclo de execução concluído com sucesso")
                logger.debug(f"Resultados: {resultados}")
                time.sleep(15)  # Pausa entre ciclos
            except Exception as e:
                logger.error(f"Erro no ciclo: {e}")
                break
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)

    finally:
        if "gerente_plugin" in locals():
            gerente_plugin.finalizar()


if __name__ == "__main__":
    main()
