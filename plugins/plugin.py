# plugin.py
# Plugin Base Class com Autoregistro e suporte a detecção inteligente de dependências

from typing import Dict, Optional, Any, List, Type
import numpy as np
import inspect
from utils.logging_config import get_logger

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

        Ignora parâmetros padrão como 'gerente', '*args', '**kwargs'.
        """
        plugin_cls = cls.obter_plugin(nome)
        if not plugin_cls:
            return []

        try:
            sig = inspect.signature(plugin_cls.__init__)
            params = list(sig.parameters.values())[1:]  # Ignora 'self'
            deps = [
                p.name
                for p in params
                if p.name not in ("gerente", "args", "kwargs")
                and not p.name.startswith("_")
            ]
            return deps
        except Exception as e:
            logger.error(f"Erro ao inspecionar dependências de {nome}: {e}")
            return []


class Plugin:
    """
    Classe base para plugins.

    Atributos esperados:
        PLUGIN_NAME: Nome único
        PLUGIN_CATEGORIA: Ex: "plugin", "gerenciador"
        PLUGIN_TAGS: Lista de strings
        PLUGIN_PRIORIDADE: Prioridade de carga
    """

    PLUGIN_NAME: Optional[str] = None
    PLUGIN_CATEGORIA: str = "plugin"
    PLUGIN_TAGS: List[str] = []
    PLUGIN_PRIORIDADE: int = 100

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        PluginRegistry.registrar(cls)

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

    def inicializar(self, config: Dict[str, Any]) -> bool:
        try:
            if self.inicializado:
                return True
            self._config = config
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
        try:
            if not self.inicializado:
                logger.error(f"Plugin {self.nome} não inicializado")
                return False

            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros obrigatórios ausentes em {self.nome}")
                return False

            if not isinstance(dados_completos, dict):
                logger.warning(f"dados_completos inválido em {self.nome}")
                return False

            return True
        except Exception as e:
            logger.error(f"Erro ao executar plugin {self.nome}: {e}")
            return False

    def finalizar(self):
        try:
            if not self.inicializado:
                return
            self._config = None
            self._dependencias.clear()
            self.inicializado = False
            logger.info(f"Plugin {self.nome} finalizado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao finalizar plugin {self.nome}: {e}")

    def _extrair_dados(
        self, dados_completos: List[Any], indices: List[int]
    ) -> Dict[int, np.ndarray]:
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
        except Exception as e:
            logger.error(f"Erro ao extrair dados em {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}
