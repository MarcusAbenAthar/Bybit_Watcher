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
    Classe base para todos os gerenciadores do sistema Bybit_Watcher.

    Regras:
    - PLUGIN_NAME obrigatório e único.
    - Implementar o método dependencias(), retornando lista de nomes de dependências (strings).
    - Implementar o método identificar_plugins(), retornando o nome do gerenciador.
    - Documentação clara via docstring e comentários.
    - Suporte à autoidentificação, auto plug-in e injeção dinâmica de dependências.
    """
    PLUGIN_NAME: str = None

    _REGISTRO_GERENCIADORES: Dict[str, Type["BaseGerenciador"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registrar_gerenciador(cls)
        if not getattr(cls, "PLUGIN_NAME", None):
            raise ValueError(f"{cls.__name__} precisa definir PLUGIN_NAME.")
        if not hasattr(cls, "dependencias"):
            logger.warning(f"{cls.__name__} deveria implementar o método dependencias().")
        if not hasattr(cls, "identificar_plugins"):
            logger.warning(f"{cls.__name__} deveria implementar o método identificar_plugins().")

    @classmethod
    def dependencias(cls) -> List[str]:
        """
        Retorna lista de nomes (strings) das dependências obrigatórias do gerenciador.
        Deve ser sobrescrito nas subclasses.
        """
        return []

    @classmethod
    def identificar_plugins(cls) -> str:
        """
        Retorna o nome do gerenciador para autoidentificação.
        Deve ser sobrescrito nas subclasses.
        """
        return getattr(cls, "PLUGIN_NAME", cls.__name__)

    # Os demais métodos e atributos permanecem conforme já implementados, mantendo compatibilidade e clareza.

    _REGISTRO_GERENCIADORES: Dict[str, Type["BaseGerenciador"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registrar_gerenciador(cls)

    def __init__(self, **kwargs):
        self._config = {}
        self.inicializado = False

    def finalizar(self) -> bool:
        """
        Finaliza o gerenciador, limpando configurações e dependências básicas.
        Pode ser sobrescrito por subclasses para shutdown mais criterioso.
        Retorna:
            bool: True se finalizado com sucesso, False caso contrário.
        """
        try:
            if not self.inicializado:
                return True
            self._config = {}
            self.inicializado = False
            logger.info(f"{self.__class__.__name__} finalizado com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao finalizar {self.__class__.__name__}: {e}")
            return False

    @classmethod
    def registrar_gerenciador(cls, gerenciador_cls: Type["BaseGerenciador"]):
        """
        Registra um gerenciador no sistema.

        Args:
            gerenciador_cls: Classe do gerenciador a ser registrado.

        Raises:
            ValueError: Se a classe não herdar de BaseGerenciador.
        """
        nome = getattr(gerenciador_cls, "PLUGIN_NAME", gerenciador_cls.__name__)
        if (
            not issubclass(gerenciador_cls, BaseGerenciador)
            or gerenciador_cls is BaseGerenciador
        ):
            raise ValueError(
                f"{gerenciador_cls.__name__} deve herdar de BaseGerenciador."
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
            config: Dicionário com configurações necessárias.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
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
        except KeyError as e:
            logger.error(
                f"Chave de configuração ausente para {self.__class__.__name__}: {e}"
            )
            return False
        except TypeError as e:
            logger.error(
                f"Erro de tipo na configuração de {self.__class__.__name__}: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Erro inesperado ao inicializar {self.__class__.__name__}: {e}"
            )
            return False

    def executar(self, *args, **kwargs):
        """Executa a lógica principal do gerenciador."""
        raise NotImplementedError("Gerenciador precisa implementar executar()")
