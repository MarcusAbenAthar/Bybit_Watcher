# plugin.py
# Plugin Base Class com Autoregistro e suporte a detecção inteligente de dependências

from __future__ import annotations
import inspect
from typing import TYPE_CHECKING, Dict, Optional, Any, List, Type
import numpy as np
import logging
from utils.logging_config import get_logger, log_banco, log_banco

if TYPE_CHECKING:
    from plugins.gerenciadores.gerenciador import BaseGerenciador

logger = get_logger(__name__)


class PluginRegistry:
    """
    Registro global de plugins baseado no PLUGIN_NAME.
    """

    _registry: Dict[str, Type["Plugin"]] = {}

    @classmethod
    def registrar(cls, plugin_cls: Type["Plugin"]):
        plugin_name = getattr(plugin_cls, "PLUGIN_NAME", None)
        if not plugin_name:
            raise ValueError(f"{plugin_cls.__name__} precisa definir PLUGIN_NAME.")
        if not issubclass(plugin_cls, Plugin) or plugin_cls is Plugin:
            raise ValueError(f"{plugin_cls.__name__} deve herdar de Plugin.")
        if plugin_name in cls._registry:
            logger.warning(f"Plugin '{plugin_name}' já registrado. Substituindo...")
        cls._registry[plugin_name] = plugin_cls
        logger.debug(f"Plugin registrado: {plugin_name}")

    @classmethod
    def obter_plugin(cls, nome: str) -> Optional[Type["Plugin"]]:
        return cls._registry.get(nome)

    @classmethod
    def todos(cls) -> Dict[str, Type["Plugin"]]:
        return cls._registry.copy()

    @classmethod
    def dependencias_para(cls, nome: str) -> List[str]:
        """
        Coleta dinamicamente as dependências do construtor (__init__) do plugin.

        Ignora parâmetros padrão como 'gerente', '*args', '**kwargs' e considera apenas
        parâmetros anotados como subclasses de Plugin.
        """
        plugin_cls = cls.obter_plugin(nome)
        if not plugin_cls:
            return []

        try:
            sig = inspect.signature(plugin_cls.__init__)
            params = list(sig.parameters.values())[1:]  # Ignora 'self'
            deps = []
            for p in params:
                if p.name in ("gerente", "args", "kwargs") or p.name.startswith("_"):
                    continue
                # Verifica se o parâmetro é anotado como Plugin ou subclasse
                if p.annotation and p.annotation is not inspect.Parameter.empty:
                    if isinstance(p.annotation, type) and issubclass(
                        p.annotation, Plugin
                    ):
                        deps.append(p.name)
            return deps
        except Exception as e:
            logger.error(f"Erro ao inspecionar dependências de {nome}: {e}")
            return []


class Plugin:
    """
    Classe base para todos os plugins do sistema.

    Atributos Obrigatórios:
        PLUGIN_NAME (str): Nome único do plugin
        PLUGIN_CATEGORIA (str): Categoria do plugin (ex: 'indicador', 'analise', etc)
        PLUGIN_TAGS (List[str]): Tags para categorização
        PLUGIN_SCHEMA_VERSAO (str): Versão do schema do plugin
    """

    PLUGIN_NAME: str = None
    PLUGIN_CATEGORIA: str = None
    PLUGIN_TAGS: List[str] = []
    PLUGIN_SCHEMA_VERSAO: str = "1.0"
    PLUGIN_TABELAS: Dict[str, Dict] = {}

    def __init_subclass__(cls, **kwargs):
        """Registra automaticamente subclasses e valida atributos obrigatórios."""
        super().__init_subclass__(**kwargs)

        # Valida atributos obrigatórios
        if not getattr(cls, "PLUGIN_NAME", None):
            raise ValueError(f"{cls.__name__} precisa definir PLUGIN_NAME")

        if not getattr(cls, "PLUGIN_CATEGORIA", None):
            raise ValueError(f"{cls.__name__} precisa definir PLUGIN_CATEGORIA")

        if not getattr(cls, "PLUGIN_TAGS", None):
            raise ValueError(f"{cls.__name__} precisa definir PLUGIN_TAGS")

        if not getattr(cls, "PLUGIN_SCHEMA_VERSAO", None):
            cls.PLUGIN_SCHEMA_VERSAO = "1.0"  # Valor padrão

        # Registra o plugin
        PluginRegistry.registrar(cls)

    def __init__(self, gerente=None, **kwargs):
        """
        Inicializa o plugin com gerente e argumentos opcionais.

        Args:
            gerente: Instância do gerenciador de plugins
            **kwargs: Argumentos adicionais específicos do plugin
        """
        self.gerente = gerente
        self.inicializado = False
        self._config = {}

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações necessárias

        Returns:
            bool: True se inicializado com sucesso, False caso contrário
        """
        try:
            if self.inicializado:
                return True

            self._config = config
            self.inicializado = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar {self.PLUGIN_NAME}: {str(e)}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a lógica principal do plugin.
        Deve ser implementado pelas subclasses.
        """
        raise NotImplementedError("Plugin precisa implementar executar()")

    def finalizar(self) -> bool:
        """
        Finaliza o plugin, limpando recursos e conexões.

        Returns:
            bool: True se finalizado com sucesso, False caso contrário
        """
        try:
            if not self.inicializado:
                return True

            self._config = {}
            self.inicializado = False
            return True

        except Exception as e:
            logger.error(f"Erro ao finalizar {self.PLUGIN_NAME}: {str(e)}")
            return False

    @property
    def plugin_tabelas(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna um dicionário com as definições das tabelas do plugin.
        Deve ser sobrescrito nas subclasses que precisam de tabelas.

        Returns:
            Dict[str, Dict[str, Any]]: Dicionário no formato:
                {
                    "nome_tabela": {
                        "columns": {
                            "coluna1": "TIPO_SQL",
                            "coluna2": "TIPO_SQL"
                        },
                        "plugin": "nome_do_plugin"
                    }
                }
        """
        return {}

    @property
    def plugin_schema_versao(self) -> str:
        """
        Retorna a versão do schema do plugin.
        Deve ser sobrescrito nas subclasses que precisam de tabelas.

        Returns:
            str: Versão do schema no formato "X.Y"
        """
        return "1.0"

    # Os demais métodos e atributos permanecem conforme já implementados, mantendo compatibilidade e clareza.

    def __init__(self, **kwargs):
        self._nome = self.PLUGIN_NAME or self.__class__.__name__
        self.categoria = self.PLUGIN_CATEGORIA
        self.tags = self.PLUGIN_TAGS
        self.prioridade = self.PLUGIN_PRIORIDADE
        self.tipo = getattr(self, "PLUGIN_TYPE", "adicional")
        self.descricao = ""
        self.inicializado = False
        self._config = None
        self._dependencias: List[Plugin] = []

        for nome, dependencia in kwargs.items():
            if isinstance(dependencia, Plugin):
                setattr(self, f"_{nome}", dependencia)
                self._dependencias.append(dependencia)

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str):
        self._nome = valor
        if not self.PLUGIN_NAME:
            self.PLUGIN_NAME = valor

    def configuracoes_requeridas(self) -> List[str]:
        """
        Retorna lista de chaves obrigatórias no config.
        Subclasses devem sobrescrever este método se houver configurações específicas.
        """
        return []

    def _extrair_dados(
        self, dados_completos: List[Any], indices: List[int]
    ) -> Dict[int, np.ndarray]:
        """
        Extrai dados numéricos de uma lista de candles.

        Args:
            dados_completos: Lista de candles.
            indices: Lista de índices para extrair.

        Returns:
            Dict[int, np.ndarray]: Dicionário com arrays numéricos para cada índice.
        """
        try:
            valores = {idx: [] for idx in indices}
            for candle in dados_completos:
                if any(
                    candle[i] is None or str(candle[i]).strip() == "" for i in indices
                ):
                    continue
                try:
                    for idx in indices:
                        valor = float(
                            str(candle[idx]).replace("e", "").replace("E", "")
                        )
                        valores[idx].append(valor)
                except (ValueError, TypeError):
                    continue
            if not all(valores.values()):
                logger.warning(f"Dados incompletos em {self.nome}")
                return {idx: np.array([]) for idx in indices}
            return {idx: np.array(valores[idx], dtype=np.float64) for idx in indices}
        except IndexError as e:
            logger.error(f"Índice inválido em dados_completos para {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}
        except TypeError as e:
            logger.error(f"Erro de tipo nos dados para {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair dados em {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}

    @property
    def should_log_banco(self) -> bool:
        """
        Determina se o plugin deve registrar logs de banco.
        Padrão: True se declarar PLUGIN_TABELAS
        """
        return hasattr(self, "PLUGIN_TABELAS")
