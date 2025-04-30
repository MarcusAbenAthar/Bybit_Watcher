"""
Bot de análise de mercado cripto seguindo as Regras de Ouro.
"""

import sys
import time
from utils.logging_config import get_logger
from utils.config import carregar_config
from utils.handlers import registrar_sinais
from plugins.gerenciadores.gerenciador import BaseGerenciador
from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.schema_generator import generate_schema

logger = get_logger(__name__)


def iniciar_bot(config: dict) -> tuple:
    """
    Configura e inicia os gerenciadores do sistema.

    Args:
        config: Dicionário de configurações carregado por config.py.

    Returns:
        tuple: (gerenciador_bot, gerente) inicializados.

    Raises:
        ValueError: Se config for inválido.
        RuntimeError: Se a inicialização de gerenciadores falhar.
    """
    try:
        if not isinstance(config, dict):
            raise ValueError("Configuração inválida: deve ser um dicionário")

        logger.info("Inicializando bot de mercado...")

        gerente = GerenciadorPlugins()
        if not gerente.inicializar(config):
            raise RuntimeError("Falha ao inicializar GerenciadorPlugins")

        gerenciador_cls = BaseGerenciador.obter_gerenciador("gerenciador_bot")
        if not gerenciador_cls:
            raise RuntimeError("GerenciadorBot não registrado")

        gerenciador_bot = gerenciador_cls(gerente=gerente)
        if not gerenciador_bot.inicializar(config):
            raise RuntimeError("Falha ao inicializar GerenciadorBot")

        if not gerenciador_bot.iniciar():
            raise RuntimeError("Falha ao iniciar GerenciadorBot")

        def finalizar():
            """Callback para finalizar gerenciadores."""
            try:
                gerenciador_bot.finalizar()
                gerente.finalizar()
                logger.info("Bot finalizado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao finalizar bot: {e}", exc_info=True)

        registrar_sinais(finalizar)
        return gerenciador_bot, gerente

    except Exception as e:
        logger.error(f"Erro ao iniciar bot: {e}", exc_info=True)
        raise


def loop_principal(gerenciador_bot, gerente, cycle_interval: float):
    """
    Executa o loop principal do bot.

    Args:
        gerenciador_bot: Instância de GerenciadorBot.
        gerente: Instância de GerenciadorPlugins.
        cycle_interval: Intervalo entre ciclos (segundos).
    """
    while True:
        try:
            logger.info("Iniciando ciclo de execução")
            if not gerenciador_bot.executar():
                logger.warning("Ciclo com falha parcial. Continuando...")
            else:
                logger.info("Ciclo concluído com sucesso")
            time.sleep(cycle_interval)
        except KeyboardInterrupt:
            logger.info("Encerramento solicitado pelo usuário (Ctrl+C)")
            gerenciador_bot.finalizar()
            gerente.finalizar()
            break
        except ConnectionError as e:
            logger.warning(f"Erro de conexão temporário: {e}. Tentando novamente...")
            time.sleep(cycle_interval * 2)
            continue
        except Exception as e:
            logger.error(f"Erro no ciclo principal: {e}", exc_info=True)
            time.sleep(cycle_interval * 2)
            continue  # Resiliência para erros genéricos


def main():
    """
    Ponto de entrada principal do bot.
    Integra monitoramento contínuo institucional e monitoramento prioritário de ordens abertas.
    """
    try:
        # Gera schema JSON antes de iniciar o banco
        generate_schema()
        config = carregar_config()
        if not config:
            logger.critical("Falha ao carregar configurações")
            sys.exit(1)

        # Obter intervalo de ciclo configurável
        cycle_interval = config.get("bot", {}).get("cycle_interval", 15.0)
        if not isinstance(cycle_interval, (int, float)) or cycle_interval <= 0:
            logger.warning(
                f"cycle_interval inválido: {cycle_interval}. Usando padrão: 15s"
            )
            cycle_interval = 15.0

        gerenciador_bot, gerente = iniciar_bot(config)

        loop_principal(gerenciador_bot, gerente, cycle_interval)

    except Exception as e:
        logger.critical(f"Erro fatal ao executar o bot: {e}", exc_info=True)
        sys.exit(1)


from utils.schema_generator import generate_schema
if __name__ == "__main__":
    try:
        generate_schema()
    except Exception as e:
        import logging
        logging.error(f"[main] Falha ao gerar schema: {e}")
        raise SystemExit(1)
    main()
