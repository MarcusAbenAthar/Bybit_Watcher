import signal
import sys
from typing import Callable, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


def signal_handler(
    signum: int, frame=None, finalizar_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Handler para sinais de interrupção do sistema operacional.

    Args:
        signum (int): Código do sinal recebido (ex: SIGINT, SIGTERM).
        frame: Quadro atual da pilha de execução (não utilizado).
        finalizar_callback: Função opcional para finalizar recursos antes de encerrar.
    """
    sinais = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM (Encerramento)",
    }
    descricao = sinais.get(signum, f"Sinal desconhecido ({signum})")
    logger.info(
        f"[SignalHandler] Recebido sinal: {descricao} (código {signum}). Encerrando com segurança..."
    )

    if finalizar_callback:
        try:
            finalizar_callback()
        except Exception as e:
            logger.error(f"Erro ao executar callback de finalização: {e}")

    sys.exit(0)


def registrar_sinais(finalizar_callback: Optional[Callable[[], None]] = None) -> None:
    """
    Registra os handlers para os sinais de encerramento.

    Args:
        finalizar_callback: Função opcional para finalizar recursos antes de encerrar.
    """

    def handler_wrapper(signum: int, frame=None) -> None:
        signal_handler(signum, frame, finalizar_callback)

    signal.signal(signal.SIGINT, handler_wrapper)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handler_wrapper)
    logger.debug("[SignalHandler] Registrado para SIGINT e SIGTERM")
