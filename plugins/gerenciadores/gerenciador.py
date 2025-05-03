# gerenciador.py
# Classe base para todos os gerenciadores do sistema

"""
Base abstrata para gerenciadores (como Bot, Banco, Plugins).
Incorpora sistema de auto-registro semelhante ao Plugin.
"""

from typing import Type, Dict, List
from utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseGerenciador:
    """
    Classe base para todos os gerenciadores do sistema.

    Atributos Obrigatórios:
        PLUGIN_NAME (str): Nome único do gerenciador
        PLUGIN_CATEGORIA (str): Sempre 'gerenciador'
        PLUGIN_TAGS (List[str]): Tags para categorização
        PLUGIN_SCHEMA_VERSAO (str): Versão do schema do gerenciador
    """

    PLUGIN_NAME: str = None
    PLUGIN_CATEGORIA: str = "gerenciador"
    PLUGIN_TAGS: List[str] = []
    PLUGIN_SCHEMA_VERSAO: str = "1.0"
    PLUGIN_TABELAS: Dict[str, Dict] = {}

    _REGISTRO_GERENCIADORES: Dict[str, Type["BaseGerenciador"]] = {}

    def __init_subclass__(cls, **kwargs):
        """Registra automaticamente subclasses e valida atributos obrigatórios."""
        super().__init_subclass__(**kwargs)

        # Valida atributos obrigatórios
        if not getattr(cls, "PLUGIN_NAME", None):
            raise ValueError(f"{cls.__name__} precisa definir PLUGIN_NAME")

        if not getattr(cls, "PLUGIN_TAGS", None):
            raise ValueError(f"{cls.__name__} precisa definir PLUGIN_TAGS")

        if not getattr(cls, "PLUGIN_SCHEMA_VERSAO", None):
            cls.PLUGIN_SCHEMA_VERSAO = "1.0"  # Valor padrão

        # Registra o gerenciador
        cls.registrar_gerenciador(cls)

    @classmethod
    def registrar_gerenciador(cls, gerenciador_cls: Type["BaseGerenciador"]):
        """
        Registra um gerenciador no sistema.

        Args:
            gerenciador_cls: Classe do gerenciador a ser registrado

        Raises:
            ValueError: Se a classe não herdar de BaseGerenciador
        """
        nome = getattr(gerenciador_cls, "PLUGIN_NAME", gerenciador_cls.__name__)
        if (
            not issubclass(gerenciador_cls, BaseGerenciador)
            or gerenciador_cls is BaseGerenciador
        ):
            raise ValueError(
                f"{gerenciador_cls.__name__} deve herdar de BaseGerenciador"
            )

        if nome in cls._REGISTRO_GERENCIADORES:
            logger.warning(f"Gerenciador {nome} já registrado. Ignorando.")
        else:
            cls._REGISTRO_GERENCIADORES[nome] = gerenciador_cls
            logger.debug(f"Gerenciador {nome} registrado com sucesso.")

    @classmethod
    def obter_gerenciador(cls, nome: str) -> Type["BaseGerenciador"]:
        """Retorna a classe do gerenciador registrado com o nome especificado."""
        return cls._REGISTRO_GERENCIADORES.get(nome)

    @classmethod
    def listar_gerenciadores(cls) -> Dict[str, Type["BaseGerenciador"]]:
        """Retorna uma cópia do registro de gerenciadores."""
        return cls._REGISTRO_GERENCIADORES.copy()

    def __init__(self, **kwargs):
        """
        Inicializa o gerenciador com argumentos opcionais.

        Args:
            **kwargs: Argumentos adicionais específicos do gerenciador
        """
        self._config = {}
        self.inicializado = False

    def configuracoes_requeridas(self) -> List[str]:
        """
        Retorna lista de chaves obrigatórias no config.
        Subclasses devem sobrescrever este método se houver configurações específicas.
        """
        return []

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o gerenciador com a configuração fornecida.

        Args:
            config: Dicionário com configurações necessárias

        Returns:
            bool: True se inicializado com sucesso, False caso contrário
        """
        try:
            if self.inicializado:
                return True

            requeridas = self.configuracoes_requeridas()
            if not all(k in config for k in requeridas):
                logger.error(
                    f"Configuração incompleta para {self.__class__.__name__}: faltam {requeridas}"
                )
                return False

            self._config = config
            self.inicializado = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar {self.__class__.__name__}: {str(e)}")
            return False

    def executar(self, *args, **kwargs):
        """
        Executa a lógica principal do gerenciador.
        Deve ser implementado pelas subclasses.
        """
        raise NotImplementedError("Gerenciador precisa implementar executar()")

    def finalizar(self) -> bool:
        """
        Finaliza o gerenciador, limpando recursos e conexões.

        Returns:
            bool: True se finalizado com sucesso, False caso contrário
        """
        try:
            if not self.inicializado:
                return True

            self._config = {}
            self.inicializado = False
            logger.debug(f"{self.__class__.__name__} finalizado com sucesso.")
            return True

        except Exception as e:
            logger.error(f"Erro ao finalizar {self.__class__.__name__}: {str(e)}")
            return False
