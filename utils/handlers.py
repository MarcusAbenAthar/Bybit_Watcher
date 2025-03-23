# handlers.py
from utils.logging_config import get_logger
import sys

logger = get_logger(__name__)


def signal_handler(signum: int, frame=None) -> None:
    """Handler para sinais de interrupção."""
    logger.info(f"Recebido sinal de interrupção ({signum}). Encerrando...")
    sys.exit(0)
