"""Plugin para operações de gravação no banco de dados."""

from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class BancoDados(Plugin):
    """Plugin responsável por registrar dados de análise no banco de dados."""

    PLUGIN_NAME = "banco_dados"
    PLUGIN_CATEGORIA = "infraestrutura"
    PLUGIN_TAGS = ["persistencia", "infraestrutura"]
    PLUGIN_PRIORIDADE = 20

    def __init__(self, gerenciador_banco=None, **kwargs):
        """
        Inicializa o plugin BancoDados com o gerenciador injetado.

        Args:
            gerenciador_banco: Instância do GerenciadorBanco (injetada automaticamente)
            **kwargs: Outras dependências, se houver.
        """
        super().__init__(**kwargs)
        self._gerenciador_banco = gerenciador_banco

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin e valida o GerenciadorBanco.

        Args:
            config: Configurações globais do sistema.

        Returns:
            bool: True se inicializado com sucesso.
        """
        try:
            if not super().inicializar(config):
                return False

            if not self._gerenciador_banco:
                logger.error("GerenciadorBanco não foi injetado corretamente")
                return False

            if not self._gerenciador_banco.inicializado:
                if not self._gerenciador_banco.inicializar(config):
                    logger.error("GerenciadorBanco não pôde ser inicializado")
                    return False

            logger.info("BancoDados inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar BancoDados: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o plugin (placeholder).

        Retorna True mas não realiza nenhuma operação,
        pois o CRUD depende da definição futura das tabelas.

        Returns:
            bool: Sempre True
        """
        logger.warning("Execução de BancoDados ignorada (sem CRUD implementado)")
        return True

    def finalizar(self):
        """
        Finaliza o plugin (sem fechar conexões).

        O encerramento de conexões é responsabilidade do GerenciadorBanco.
        """
        try:
            logger.info("Finalizando BancoDados (sem ações de conexão)")
        except Exception as e:
            logger.error(f"Erro ao finalizar BancoDados: {e}", exc_info=True)
