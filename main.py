"""Bot de análise de mercado cripto seguindo as Regras de Ouro."""

import logging
import signal
import sys
import time
from dotenv import load_dotenv
from plugins.gerenciadores.gerenciador_bot import GerenciadorBot
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.config import carregar_config
from utils.handlers import signal_handler
from utils.logging_config import configurar_logging

load_dotenv()
logger = logging.getLogger(__name__)

PLUGINS_ESSENCIAIS = {
    "plugins.conexao": "Conexão com a Bybit",
    "plugins.gerenciadores.gerenciador_banco": "Gerenciador do Banco",
    "plugins.banco_dados": "Banco de Dados",
    "plugins.validador_dados": "Validação de Dados",
    "plugins.calculo_alavancagem": "Cálculo de Alavancagem",
    "plugins.indicadores.indicadores_tendencia": "Indicadores de Tendência",
    "plugins.medias_moveis": "Médias Móveis",
    "plugins.analise_candles": "Análise de Candlestick",
    "plugins.price_action": "Análise de Price Action",
    "plugins.calculo_risco": "Cálculo de Risco",
    "plugins.indicadores.indicadores_osciladores": "Indicadores Osciladores",
    "plugins.indicadores.indicadores_volatilidade": "Indicadores de Volatilidade",
    "plugins.indicadores.indicadores_volume": "Indicadores de Volume",
    "plugins.indicadores.outros_indicadores": "Outros Indicadores",
    "plugins.analisador_mercado": "Analisador de Mercado",
}

PLUGINS_ADICIONAIS = {
    "plugins.sinais_plugin": "Gerador de Sinais",
    "plugins.execucao_ordens": "Execução de Ordens",
}


def inicializar_bot(config: dict) -> GerentePlugin:
    """
    Inicializa o bot de forma segura.

    Args:
        config (dict): Configurações do bot

    Returns:
        GerentePlugin: Gerenciador inicializado

    Raises:
        RuntimeError: Se falhar a inicialização
    """
    try:
        gerente = GerentePlugin()
        gerente.inicializar(config)
        logger.debug("GerentePlugin inicializado")

        for plugin_name, descricao in PLUGINS_ESSENCIAIS.items():
            logger.debug(
                f"Tentando carregar plugin essencial: {plugin_name} ({descricao})"
            )
            if not gerente.carregar_plugin(plugin_name):
                logger.error(f"Falha ao carregar {plugin_name}")
                raise RuntimeError(f"Falha ao carregar plugin essencial: {plugin_name}")
            logger.info(f"Plugin essencial carregado: {plugin_name}")

        for plugin_name, descricao in PLUGINS_ADICIONAIS.items():
            logger.debug(
                f"Tentando carregar plugin adicional: {plugin_name} ({descricao})"
            )
            if not gerente.carregar_plugin(plugin_name):
                logger.warning(f"Falha ao carregar plugin adicional: {plugin_name}")
            else:
                logger.info(f"Plugin adicional carregado: {plugin_name}")

        return gerente
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        raise RuntimeError(f"Falha ao inicializar bot: {e}")


def main() -> None:
    """Função principal do bot."""
    try:
        # Carregar config e configurar logging
        config = carregar_config()
        configurar_logging(config)
        logger.info("Iniciando bot...")
        signal.signal(signal.SIGINT, signal_handler)

        gerente_plugin = inicializar_bot(config)
        gerenciador_bot = GerenciadorBot(gerente_plugin)
        if not gerenciador_bot.inicializar(config):
            raise RuntimeError("Falha ao inicializar gerenciador do bot")

        if not gerenciador_bot.iniciar():
            raise RuntimeError("Falha ao iniciar gerenciador do bot")
        logger.info("Bot iniciado com sucesso")

        while True:
            try:
                logger.execution("Iniciando ciclo de execução")
                if not gerenciador_bot.executar():
                    logger.warning("Falha no ciclo do gerenciador do bot")
                logger.execution("Ciclo de execução concluído")
                time.sleep(15)
            except Exception as e:
                logger.error(f"Erro no ciclo: {e}")
                break
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
