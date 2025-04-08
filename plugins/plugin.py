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
import numpy as np
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

    PLUGIN_NAME: Optional[str] = None
    PLUGIN_TYPE: Optional[str] = None

    def __init__(self, **kwargs):
        self._nome = self.PLUGIN_NAME if self.PLUGIN_NAME else ""
        self.descricao = ""
        self.tipo = self.PLUGIN_TYPE if self.PLUGIN_TYPE else ""
        self.inicializado = False
        self._config = None
        self._dependencias: List[Plugin] = []

        for nome, dependencia in kwargs.items():
            setattr(self, f"_{nome}", dependencia)
            if isinstance(dependencia, Plugin):
                self._dependencias.append(dependencia)

    @property
    def nome(self):
        if hasattr(self, "_nome"):
            return self._nome
        return self.PLUGIN_NAME if self.PLUGIN_NAME else ""

    @nome.setter
    def nome(self, valor):
        self._nome = valor
        if not self.PLUGIN_NAME:
            self.PLUGIN_NAME = valor

    def _extrair_dados(
        self, dados_completos: List[Any], indices: List[int]
    ) -> Dict[int, np.ndarray]:
        """
        Extrai e valida dados de candles para índices especificados.

        Args:
            dados_completos: Lista de candles
            indices: Índices dos valores a extrair (ex.: 2=high, 4=close)

        Returns:
            Dict com arrays numpy para cada índice ou arrays vazios se inválido
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
        """
        Executa o ciclo do plugin.

        Args:
            *args: Argumentos posicionais (ignorados)
            **kwargs: Argumentos nomeados esperados:
                dados (List): Lista de candles
                symbol (str): Símbolo do par
                timeframe (str): Timeframe da análise

        Returns:
            bool: True se executado com sucesso
        """
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
