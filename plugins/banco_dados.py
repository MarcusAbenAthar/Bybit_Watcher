# banco_dados.py
"""Plugin responsável por intermediar operações com o GerenciadorBanco."""

from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class BancoDados(Plugin):
    """
    Plugin essencial para comunicação com o banco.

    NOTA: Este plugin não implementa o CRUD por enquanto,
    pois as tabelas ainda não estão definidas no sistema.
    """

    PLUGIN_NAME = "banco_dados"
    PLUGIN_TYPE = "essencial"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gerenciador_banco = kwargs.get("gerenciador_banco")

    def inicializar(self, config: dict) -> bool:
        try:
            if not super().inicializar(config):
                return False

            if not self._gerenciador_banco:
                logger.error("GerenciadorBanco não fornecido para BancoDados")
                return False

            if not self._gerenciador_banco.inicializado:
                self._gerenciador_banco.inicializar(config)

            logger.info("BancoDados inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar BancoDados: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Método reservado para futuras operações de inserção/consulta.
        """
        logger.warning("BancoDados: Nenhuma operação implementada ainda.")
        return True

    def finalizar(self):
        try:
            logger.info("Finalizando BancoDados (sem encerrar conexão).")
        except Exception as e:
            logger.error(f"Erro ao finalizar BancoDados: {e}")
