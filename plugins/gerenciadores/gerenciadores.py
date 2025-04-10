# gerenciadores.py
# Classe base para todos os gerenciadores do sistema

"""
Base abstrata para gerenciadores (como Bot, Banco, Plugins).
Incorpora sistema de auto-registro semelhante ao Plugin.
"""

from typing import Type, Dict
from utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseGerenciador:
    """Classe base para todos os gerenciadores."""

    _REGISTRO_GERENCIADORES: Dict[str, Type["BaseGerenciador"]] = {}

    @classmethod
    def registrar_gerenciador(cls, gerenciador_cls: Type["BaseGerenciador"]):
        """
        Registra automaticamente a classe filha no dicionário interno.
        """
        nome = getattr(gerenciador_cls, "PLUGIN_NAME", gerenciador_cls.__name__)
        if nome in cls._REGISTRO_GERENCIADORES:
            logger.warning(f"Gerenciador {nome} já registrado. Ignorando.")
        else:
            cls._REGISTRO_GERENCIADORES[nome] = gerenciador_cls
            logger.debug(f"Gerenciador {nome} registrado com sucesso.")

    @classmethod
    def obter_gerenciador(cls, nome: str) -> Type["BaseGerenciador"]:
        """
        Retorna a classe do gerenciador pelo nome.
        """
        return cls._REGISTRO_GERENCIADORES.get(nome)

    @classmethod
    def listar_gerenciadores(cls) -> Dict[str, Type["BaseGerenciador"]]:
        """
        Lista todos os gerenciadores registrados.
        """
        return cls._REGISTRO_GERENCIADORES.copy()

    def inicializar(self, config: dict) -> bool:
        """
        Método base de inicialização. Deve ser sobrescrito pelos filhos.
        """
        raise NotImplementedError("Gerenciador precisa implementar inicializar()")

    def executar(self, *args, **kwargs):
        """
        Método base de execução. Deve ser sobrescrito pelos filhos.
        """
        raise NotImplementedError("Gerenciador precisa implementar executar()")
