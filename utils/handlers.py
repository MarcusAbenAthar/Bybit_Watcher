# handlers.py
# Description: Módulo com handlers para sinais de interrupção.

import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handler para sinais de interrupção."""
    logger.info("Recebido sinal de interrupção...")
    sys.exit(0)
