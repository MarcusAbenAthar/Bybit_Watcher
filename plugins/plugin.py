# plugin.py
# Plugin Base Class com Autoregistro por PLUGIN_NAME

from typing import Dict, Optional, Any, List, Type
import numpy as np
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
            logger.warning(f"Plugin '{plugin_name}' já registrado. Sobrescrevendo...")
        cls._registry[plugin_name] = plugin_cls
        logger.debug(f"Plugin registrado: {plugin_name}")

    @classmethod
    def obter_plugin(cls, nome: str) -> Optional[Type["Plugin"]]:
        return cls._registry.get(nome)

    @classmethod
    def todos(cls) -> Dict[str, Type["Plugin"]]:
        return cls._registry.copy()


class Plugin:
    """
    Classe base para plugins.

    Atributos esperados:
        PLUGIN_NAME (str): Nome único do plugin
        PLUGIN_TYPE (str): Tipo ("essencial" ou "adicional")
    """

    PLUGIN_NAME: Optional[str] = None
    PLUGIN_TYPE: Optional[str] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        PluginRegistry.registrar(cls)

    def __init__(self, **kwargs):
        self._nome = self.PLUGIN_NAME or self.__class__.__name__
        self.descricao = ""
        self.tipo = self.PLUGIN_TYPE or "adicional"
        self.inicializado = False
        self._config = None
        self._dependencias: List[Plugin] = []

        for nome, dependencia in kwargs.items():
            setattr(self, f"_{nome}", dependencia)
            if isinstance(dependencia, Plugin):
                self._dependencias.append(dependencia)

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = valor
        if not self.PLUGIN_NAME:
            self.PLUGIN_NAME = valor

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
                logger.warning(f"Dados insuficientes ou inválidos em {self.nome}")
                return {idx: np.array([]) for idx in indices}
            return {idx: np.array(valores[idx], dtype=np.float64) for idx in indices}
        except Exception as e:
            logger.error(f"Erro ao extrair dados em {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}

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
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                return False

            if not isinstance(dados_completos, list) or not dados_completos:
                logger.warning(f"Dados inválidos ou vazios em {self.nome}")
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
