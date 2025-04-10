"""Bot de análise de mercado cripto seguindo as Regras de Ouro."""

import logging
import signal
import sys
import time
from dotenv import load_dotenv
from plugins.gerenciadores.gerenciadores import BaseGerenciador
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.config import carregar_config
from utils.handlers import signal_handler
from utils.logging_config import configurar_logging

load_dotenv()
logger = logging.getLogger(__name__)


def main() -> None:
    """Função principal do bot."""
    try:
        # Carregar config e configurar logging
        config = carregar_config()
        configurar_logging(config)
        logger.info("Iniciando bot...")
        signal.signal(signal.SIGINT, signal_handler)

        # Inicializa o gerente central de plugins
        gerente = GerenciadorPlugins()
        if not gerente.inicializar(config):
            raise RuntimeError("Falha ao inicializar o gerente de plugins")

        # Pega o gerenciador do bot via auto-registro
        gerenciador_cls = BaseGerenciador.obter_gerenciador("gerenciador_bot")
        if not gerenciador_cls:
            raise RuntimeError("GerenciadorBot não registrado")

        gerenciador_bot = gerenciador_cls(gerente=gerente)
        if not gerenciador_bot.inicializar(config):
            raise RuntimeError("Falha ao inicializar gerenciador do bot")

        if not gerenciador_bot.iniciar():
            raise RuntimeError("Falha ao iniciar gerenciador do bot")

        logger.info("Bot iniciado com sucesso")

        # Loop principal
        while True:
            try:
                logger.execution("Iniciando ciclo de execução")
                if not gerenciador_bot.executar():
                    logger.warning("Falha no ciclo do gerenciador do bot")
                logger.execution("Ciclo de execução concluído")
                time.sleep(15)
            except Exception as e:
                logger.error(f"Erro no ciclo: {e}", exc_info=True)
                break

    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
