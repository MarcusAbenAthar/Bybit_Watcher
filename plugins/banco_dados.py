"""Plugin para operações de gravação no banco de dados."""

registry: dict[str, list[str]] = {}

from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class BancoDados(Plugin):
    """
    Plugin para operações básicas de banco de dados.
    - Responsabilidade única: operações CRUD simples.
    - Registrar tabelas por plugin.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "banco_dados"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["banco", "dados", "persistencia"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin BancoDados.
        """
        return ["gerenciador_banco"]

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
        Inicializa o plugin BancoDados e valida o GerenciadorBanco.
        Nunca cria nem altera estrutura de tabelas: responsabilidade 100% do GerenciadorBanco.

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
            try:
                self.registrar_tabela(self.PLUGIN_NAME, "dados")  # Apenas registro lógico, não cria tabela física
            except Exception as e:
                logger.warning(f"Falha ao registrar tabela no plugin BancoDados: {e}")
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
        logger.warning(
            "Execução de BancoDados ignorada (sem CRUD implementado)")
        return True

    def finalizar(self):
        """
        Finaliza o plugin BancoDados, limpando estado e garantindo shutdown seguro.
        O encerramento de conexões é responsabilidade do GerenciadorBanco.
        """
        try:
            super().finalizar()
            logger.info(
                "BancoDados finalizado com sucesso (sem ações de conexão)")
        except Exception as e:
            logger.error(f"Erro ao finalizar BancoDados: {e}", exc_info=True)

    @classmethod
    def registrar_tabela(cls, plugin_name: str, table_name: str) -> None:
        """Registra uma tabela associada a um plugin no registry global."""
        registry.setdefault(plugin_name, []).append(table_name)
        logger.info(f"Tabela registrada: {plugin_name} -> {table_name}")

    @classmethod
    def get_tabelas_por_plugin(cls) -> dict[str, list[str]]:
        """Retorna o dicionário de tabelas registradas por plugin."""
        return registry
