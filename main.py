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

# Imports stdlib
import logging
import signal
import sys
from typing import Optional

# Imports terceiros
from dotenv import load_dotenv
import os

# Imports locais
from plugins.gerente_plugin import GerentePlugin

# Configuração inicial
load_dotenv()
logger = logging.getLogger(__name__)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

# Plugins essenciais
PLUGINS_ESSENCIAIS = ["conexao", "banco_dados", "gerenciador_bot"]

# Plugins adicionais
PLUGINS_ADICIONAIS = [
    "analise_candles",
    "calculo_alavancagem",
    "calculo_risco",
    "execucao_ordens",
    "gerenciador_banco",
    "indicadores.indicadores_osciladores",
    "indicadores.indicadores_tendencia",
    "indicadores.indicadores_volatilidade",
    "indicadores.indicadores_volume",
    "indicadores.outros_indicadores",
    "medias_moveis",
    "price_action",
    "sinais_plugin",
    "validador_dados",
]


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handler para sinais de interrupção."""
    logger.info("Recebido sinal de interrupção...")
    sys.exit(0)


def carregar_config() -> dict:
    """
    Carrega a configuração do bot de forma segura.

    Returns:
        dict: Configuração carregada
    """
    config = {"timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]}
    return config


def inicializar_bot() -> GerentePlugin:
    """
    Inicializa o bot de forma segura.

    Returns:
        GerentePlugin: Gerenciador inicializado

    Raises:
        RuntimeError: Se falhar a inicialização
    """
    try:
        # Carrega config
        config = carregar_config()

        # Inicializa gerente
        gerente = GerentePlugin()
        gerente.inicializar(config)

        # Carrega plugins essenciais
        if not gerente.carregar_plugins("plugins"):  # Removido argumento config
            raise RuntimeError("Falha ao carregar plugins essenciais")

        # Validação final
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
            gerente.interromper_execucao()


if __name__ == "__main__":
    main()
