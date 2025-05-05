"""
plugin_utils.py
Utilitário institucional para auto plug-in, auto injeção e detecção de dependências em plugins e gerenciadores.

- Descoberta dinâmica de plugins/gerenciadores via registro.
- Resolução recursiva e criteriosa de dependências.
- Injeção automática de instâncias já criadas.
- Detecção de ciclos e logs claros.
- Padrão único para todo o projeto Bybit_Watcher.

Utilitários para plugins de indicadores: ajuste de períodos, volatilidade, extração de OHLCV, validação de candles e wrappers para talib.
Padroniza e reduz redundância entre plugins, conforme as regras de ouro do projeto.
"""

from typing import Dict, Any, List, Callable, Type
from plugins.plugin import Plugin, PluginRegistry
from utils.logging_config import get_logger
import numpy as np
import talib
import logging
from functools import wraps

logger = get_logger(__name__)


def inicializar_componentes(
    nomes_classes: List[str],
    registro: Callable[[str], Type],
    config: dict,
    tipo_instancia: Any = Plugin,
) -> Dict[str, Any]:
    """
    Inicializa componentes (plugins/gerenciadores) de acordo com o padrão institucional.

    Args:
        nomes_classes (List[str]): Lista dos nomes dos componentes a inicializar.
        registro (Callable): Função para obter a classe pelo nome.
        config (dict): Configuração global.
        tipo_instancia (Any): Tipos válidos para instância (Plugin, BaseGerenciador).

    Returns:
        Dict[str, Any]: Dicionário nome -> instância inicializada.
    """
    instanciados = {}
    grafo_dependencias = {nome: registro(nome).dependencias() for nome in nomes_classes}

    def resolver(nome, pilha=None):
        if nome in instanciados:
            return instanciados[nome]
        pilha = pilha or []
        if nome in pilha:
            logger.error(
                f"[plugin_utils] Ciclo de dependências detectado: {' -> '.join(pilha + [nome])}"
            )
            raise RuntimeError(f"Ciclo de dependências: {' -> '.join(pilha + [nome])}")
        pilha.append(nome)
        classe = registro(nome)
        if not classe:
            logger.error(f"[plugin_utils] Classe '{nome}' não encontrada no registro.")
            raise RuntimeError(f"Classe '{nome}' não encontrada.")
        deps = grafo_dependencias.get(nome, [])
        kwargs = {}
        for dep in deps:
            kwargs[dep] = resolver(dep, pilha=list(pilha))
        try:
            instancia = classe(**kwargs)
            if not isinstance(instancia, tipo_instancia):
                logger.error(
                    f"Classe '{nome}' não é instância válida de {tipo_instancia}"
                )
                raise TypeError(f"Classe '{nome}' inválida.")
            if instancia.inicializar(config):
                instanciados[nome] = instancia
                logger.info(f"Componente inicializado: {nome}")
                return instancia
            else:
                logger.error(f"Falha ao inicializar componente: {nome}")
                raise RuntimeError(f"Falha ao inicializar componente: {nome}")
        except Exception as e:
            logger.error(f"Erro ao instanciar componente {nome}: {e}", exc_info=True)
            raise

    for nome in nomes_classes:
        resolver(nome)
    return instanciados


# --- Ajuste de períodos ---
def ajustar_periodos_generico(base_dict, timeframe, volatilidade=0.0):
    """
    Ajusta dinamicamente os períodos dos indicadores com base no timeframe e volatilidade.
    Args:
        base_dict (dict): Dicionário com períodos base para cada indicador.
        timeframe (str): Timeframe (ex.: '1m', '1d').
        volatilidade (float): Volatilidade calculada.
    Returns:
        dict: Períodos ajustados para indicadores.
    """
    ajuste = int(volatilidade * 10)
    fator = 1.0
    if timeframe == "1m":
        fator = 0.5
    elif timeframe == "1d":
        fator = 1.5
    return {k: max(5, int(v * fator) + ajuste) for k, v in base_dict.items()}


# --- Cálculo de volatilidade ---
def calcular_volatilidade_generico(close, periodo=14):
    """
    Calcula a volatilidade com base no desvio padrão relativo ao preço de fechamento.
    Args:
        close (np.ndarray): Array de preços de fechamento.
        periodo (int): Período para cálculo.
    Returns:
        float: Volatilidade relativa (0.0 a 1.0)
    """
    try:
        if len(close) < periodo:
            return 0.0
        std = talib.STDDEV(close, timeperiod=periodo)
        return (
            float(std[-1]) / float(close[-1])
            if std.size > 0 and close[-1] != 0
            else 0.0
        )
    except Exception as e:
        logger.error(f"[plugin_utils] Erro ao calcular volatilidade: {e}")
        return 0.0


# --- Extração de OHLCV ---
def extrair_ohlcv(klines, indices):
    """
    Extrai arrays NumPy das colunas OHLCV com base nos índices informados.
    Args:
        klines (list): Lista de k-lines.
        indices (list): Índices para extração (ex.: [2,3,4,5]).
    Returns:
        dict: Dicionário {indice: np.ndarray}
    """
    try:
        return {
            i: np.array([float(d[i]) for d in klines if len(d) > i]) for i in indices
        }
    except Exception as e:
        logger.error(f"[plugin_utils] Erro ao extrair OHLCV: {e}")
        return {i: np.array([]) for i in indices}


# --- Validação de candles ---
def validar_klines(klines, min_len=20):
    """
    Valida o formato da lista de klines (candles).
    Args:
        klines (list): Lista de k-lines.
        min_len (int): Tamanho mínimo.
    Returns:
        bool: True se válido, False caso contrário.
    """
    if not isinstance(klines, list) or len(klines) < min_len:
        return False
    for item in klines:
        if not isinstance(item, (list, tuple)) or len(item) < 5:
            return False
        for idx in [2, 3, 4]:
            try:
                float(item[idx])
            except (TypeError, ValueError):
                return False
    return True


# --- Wrapper para indicadores talib ---
def talib_wrapper(func, *args, **kwargs):
    """
    Wrapper para funções do talib com tratamento de erro padronizado.
    Args:
        func (callable): Função do talib.
        *args: Argumentos.
        **kwargs: Kwargs.
    Returns:
        Resultado do talib ou array vazio/None em caso de erro.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"[plugin_utils] Erro no talib_wrapper: {e}")
        if hasattr(func, "__name__") and "return" in func.__name__:
            return None
        return np.array([])


# --- Decorador para padronizar execução e logging ---
def executar_padrao(func):
    """
    Decorador para padronizar entrada/saída e logging dos métodos executar dos plugins.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        logger.debug(
            f"[plugin_utils] Executando {func.__name__} para {symbol}-{timeframe}"
        )
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[plugin_utils] Erro em {func.__name__}: {e}", exc_info=True)
            return None

    return wrapper


def padronizar_direcao(direcao: str) -> str:
    """
    Converte direções 'ALTA'/'BAIXA' para 'LONG'/'SHORT'. Mantém 'LATERAL' igual.
    Args:
        direcao (str): Direção original ('ALTA', 'BAIXA', 'LATERAL', etc)
    Returns:
        str: Direção padronizada ('LONG', 'SHORT', 'LATERAL')
    """
    if not isinstance(direcao, str):
        return "LATERAL"
    direcao = direcao.upper()
    if direcao == "ALTA":
        return "LONG"
    if direcao == "BAIXA":
        return "SHORT"
    if direcao in ("LONG", "SHORT", "LATERAL"):
        return direcao
    return "LATERAL"
