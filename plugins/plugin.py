# plugin.py
# Plugin Base Class

"""
Classe base para plugins do sistema.

Regras de Ouro:
1. Autonomo - Gerencia seu próprio ciclo de vida
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros
4. Certeiro - Operações precisas
5. Eficiente - Performance otimizada
6. Clareza - Bem documentado
7. Modular - Responsabilidade única
8. Plugins - Interface padronizada
9. Testável - Métodos isolados
10. Documentado - Docstrings completos
"""

from typing import Dict, Optional, Any, List
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Plugin:
    """
    Classe base para plugins.

    Atributos de Classe:
        PLUGIN_NAME (str): Nome do plugin (deve ser sobrescrito)
        PLUGIN_TYPE (str): Tipo do plugin (essencial ou adicional)

    Atributos:
        nome (str): Nome do plugin
        descricao (str): Descrição do plugin
        tipo (str): Tipo do plugin
        inicializado (bool): Estado de inicialização
        _config (dict): Configurações do plugin
        _dependencias (List[Plugin]): Lista de dependências
    """

    PLUGIN_NAME: Optional[str] = None  # Deve ser definido nas subclasses
    PLUGIN_TYPE: Optional[str] = None  # Deve ser definido nas subclasses

    def __init__(self, **kwargs):
        """
        Inicializa o plugin com valores padrão e dependências.

        Args:
            **kwargs: Dependências injetadas pelo gerenciador
        """
        # Atributos básicos
        self._nome = self.PLUGIN_NAME if self.PLUGIN_NAME else ""
        self.descricao = ""
        self.tipo = self.PLUGIN_TYPE if self.PLUGIN_TYPE else ""
        self.inicializado = False
        self._config = None
        self._dependencias: List[Plugin] = []

        # Processa dependências injetadas
        for nome, dependencia in kwargs.items():
            setattr(self, f"_{nome}", dependencia)
            if isinstance(dependencia, Plugin):
                self._dependencias.append(dependencia)

    @property
    def nome(self):
        """Nome do plugin."""
        if hasattr(self, "_nome"):
            return self._nome
        return self.PLUGIN_NAME if self.PLUGIN_NAME else ""

    @nome.setter
    def nome(self, valor):
        """Define o nome do plugin."""
        self._nome = valor
        if not self.PLUGIN_NAME:
            self.PLUGIN_NAME = valor

    def inicializar(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa o plugin com as configurações fornecidas.

        Args:
            config: Configurações do plugin

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if self.inicializado:
                return True

            self._config = config

            # Verifica dependências
            for dependencia in self._dependencias:
                if not dependencia.inicializado:
                    logger.error(
                        f"Dependência {dependencia.nome} não inicializada para {self.nome}"
                    )
                    return False

            self.inicializado = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar plugin {self.nome}: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o ciclo do plugin.

        Returns:
            bool: True se executado com sucesso
        """
        try:
            if not self.inicializado:
                logger.error(f"Plugin {self.nome} não inicializado")
                return False

            return True

        except Exception as e:
            logger.error(f"Erro ao executar plugin {self.nome}: {e}")
            return False

    def finalizar(self):
        """
        Finaliza o plugin e libera recursos.
        """
        try:
            if not self.inicializado:
                return

            # Limpa recursos
            self._config = None
            self._dependencias.clear()
            self.inicializado = False
            logger.info(f"Plugin {self.nome} finalizado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao finalizar plugin {self.nome}: {e}")
