import signal
import sys
from utils.logging_config import get_logger

logger = get_logger(__name__)


def signal_handler(signum: int, frame=None) -> None:
    """
    Handler para sinais de interrupção do sistema operacional.

    Args:
        signum (int): Código do sinal recebido (ex: SIGINT, SIGTERM).
        frame: Quadro atual da pilha de execução (não utilizado).
    """
    sinais = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM (Encerramento)",
    }
    descricao = sinais.get(signum, f"Sinal desconhecido ({signum})")
    logger.info(
        f"[SignalHandler] Recebido sinal: {descricao} (código {signum}). Encerrando com segurança..."
    )

    # 🔧 No futuro: encerrar_bot() ou outro shutdown elegante
    sys.exit(0)


def registrar_sinais():
    """
    Registra os handlers para os sinais de encerramento.
    """
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)
    logger.debug("[SignalHandler] Registrado para SIGINT e SIGTERM")


# Registro automático ao importar
registrar_sinais()
