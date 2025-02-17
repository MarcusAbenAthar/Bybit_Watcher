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
    "indicadores.indicadores_tendencia",  # Necessário para sinais
    "medias_moveis",  # Necessário para sinais
    "sinais_plugin",  # Depende dos indicadores
    "gerenciadores/gerenciador_bot",  # Depende de banco_dados e gerenciador_banco
]

# Plugins adicionais em ordem de dependência
PLUGINS_ADICIONAIS = [
    "price_action",  # Análise técnica
    "analise_candles",  # Análise técnica
    "calculo_alavancagem",
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
        if not gerenciador_bot.inicializar(gerente_plugin.config):
            raise RuntimeError("Falha ao inicializar gerenciador do bot")

        # Registra todos os plugins carregados
        for nome, plugin in gerente_plugin.plugins.items():
            if not gerenciador_bot.registrar_plugin(plugin):
                logger.error(f"Falha ao registrar plugin {nome}")
                raise RuntimeError(f"Falha ao registrar plugin {nome}")

        # Inicia o bot após todos os plugins estarem registrados
        if not gerenciador_bot.iniciar():
            raise RuntimeError("Falha ao iniciar gerenciador do bot")
        logger.info("Bot iniciado com sucesso")

        # Loop principal
        while True:
            try:
                # Inicio do ciclo de execução do bot
                logger.debug("Iniciando ciclo de execução...")

                # Executa o ciclo do gerenciador do bot
                if not gerenciador_bot.executar_ciclo():
                    logger.warning("Falha no ciclo do gerenciador do bot")
                    break

                # Obtém configurações e dados necessários
                symbol = gerenciador_bot._config.get("symbol", "BTCUSDT")
                timeframe = gerenciador_bot._config.get("timeframe", "1h")
                dados = {
                    "tendencia": {
                        "direcao": "NEUTRO",
                        "forca": "MÉDIA",
                        "confianca": 50,
                    },
                    "medias_moveis": {
                        "direcao": "NEUTRO",
                        "forca": "MÉDIA",
                        "confianca": 50,
                    },
                }

                # Executa o ciclo do gerente de plugins
                if not gerente_plugin.executar_ciclo(
                    dados, symbol, timeframe, gerenciador_bot._config
                ):
                    logger.warning("Falha no ciclo de execução dos plugins")
                    break

                # Fim do ciclo de execução do bot
                logger.debug("Ciclo de execução concluído com sucesso")

            except Exception as e:
                logger.error(f"Erro no ciclo: {e}")
                break

    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)

    finally:
        if "gerente" in locals():
            gerente_plugin.interromper_execucao()


if __name__ == "__main__":
    main()
