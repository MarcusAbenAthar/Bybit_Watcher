# handlers.py
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
        signal.SIGINT: "SIGINT (Interrupção Ctrl+C)",
        signal.SIGTERM: "SIGTERM (Encerramento)",
    }
    descricao = sinais.get(signum, f"Sinal desconhecido ({signum})")
    logger.info(f"Recebido {descricao}. Encerrando com segurança...")
    sys.exit(0)
