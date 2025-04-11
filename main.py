"""Bot de análise de mercado cripto seguindo as Regras de Ouro."""

import signal
import sys
import time
import logging
from dotenv import load_dotenv
from plugins.gerenciadores.gerenciadores import BaseGerenciador
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.config import carregar_config
from utils.handlers import signal_handler
from utils.logging_config import configurar_logging

load_dotenv()
logger = logging.getLogger(__name__)


def iniciar_bot():
    """Configura e inicia todos os gerenciadores do sistema."""
    config = carregar_config()
    configurar_logging(config)
    logger.info("Inicializando bot de mercado...")

    # Tratamento de sinais do SO
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    gerente = GerenciadorPlugins()
    if not gerente.inicializar(config):
        raise RuntimeError("Falha ao inicializar o GerenciadorPlugins")

    gerenciador_cls = BaseGerenciador.obter_gerenciador("gerenciador_bot")
    if not gerenciador_cls:
        raise RuntimeError("GerenciadorBot não registrado")

    gerenciador_bot = gerenciador_cls(gerente=gerente)
    if not gerenciador_bot.inicializar(config):
        raise RuntimeError("Falha ao inicializar GerenciadorBot")

    if not gerenciador_bot.iniciar():
        raise RuntimeError("Falha ao iniciar GerenciadorBot")

    return gerenciador_bot


def loop_principal(gerenciador_bot):
    """Executa o loop principal do bot."""
    while True:
        try:
            logger.execution("Iniciando ciclo de execução")
            if not gerenciador_bot.executar():
                logger.warning("Ciclo com falha parcial no gerenciador do bot")
            logger.execution("Ciclo concluído com sucesso")
            time.sleep(15)
        except KeyboardInterrupt:
            logger.info("Encerramento solicitado pelo usuário (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Erro no ciclo principal: {e}", exc_info=True)
            break


def main():
    try:
        gerenciador_bot = iniciar_bot()
        loop_principal(gerenciador_bot)
    except Exception as e:
        logger.critical(f"Erro fatal ao iniciar o bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
