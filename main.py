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

import logging
import signal
import sys
from typing import Optional
from dotenv import load_dotenv
import os
from plugins.gerente_plugin import GerentePlugin

# Configuração inicial
load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handler para sinais de interrupção."""
    logger.info("Recebido sinal de interrupção...")
    sys.exit(0)


def carregar_config() -> dict:
    """
    Carrega configurações do .env

    Returns:
        dict: Configurações carregadas
    """
    try:
        return {
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "database": {
                "host": os.getenv("DB_HOST", "localhost"),
                "database": os.getenv("DB_NAME", "bybit_watcher"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD"),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao carregar config: {e}")
        raise


def inicializar_bot() -> GerentePlugin:
    """
    Inicializa o bot e seus gerentes.

    Returns:
        GerentePlugin: Gerente de plugins inicializado

    Raises:
        RuntimeError: Se falhar a inicialização
    """
    try:
        # Carrega configurações
        config = carregar_config()

        # Inicializa gerente de plugins
        gerente = GerentePlugin()
        if not gerente.inicializar(config):
            raise RuntimeError("Falha ao inicializar gerente")

        # Carrega plugins (gerenciador_banco e gerenciador_bot serão carregados aqui)
        if not gerente.carregar_plugins("plugins"):
            raise RuntimeError("Falha ao carregar plugins")

        # Verifica plugins essenciais
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
        logger.info("Iniciando bot...")
        signal.signal(signal.SIGINT, signal_handler)

        # Inicialização
        gerente = inicializar_bot()
        logger.info("Bot iniciado com sucesso")

        # Loop principal
        while True:
            try:
                if not gerente.executar_ciclo():
                    logger.warning("Falha no ciclo de execução")
                    continue

            except Exception as e:
                logger.error(f"Erro no ciclo: {e}")
                continue

    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)

    finally:
        if "gerente" in locals():
            try:
                gerente.finalizar()
                logger.info("Bot finalizado")
            except Exception as e:
                logger.error(f"Erro ao finalizar: {e}")


if __name__ == "__main__":
    main()
