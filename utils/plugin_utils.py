"""
plugin_utils.py
Utilitário institucional para auto plug-in, auto injeção e detecção de dependências em plugins e gerenciadores.

- Descoberta dinâmica de plugins/gerenciadores via registro.
- Resolução recursiva e criteriosa de dependências.
- Injeção automática de instâncias já criadas.
- Detecção de ciclos e logs claros.
- Padrão único para todo o projeto Bybit_Watcher.
"""
from typing import Dict, Any, List, Callable, Type
from plugins.plugin import Plugin, PluginRegistry
from plugins.gerenciadores.gerenciador import BaseGerenciador
from utils.logging_config import get_logger

logger = get_logger(__name__)

def inicializar_componentes(
    nomes_classes: List[str],
    registro: Callable[[str], Type],
    config: dict,
    tipo_instancia: Any = (Plugin, BaseGerenciador),
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
            logger.error(f"[plugin_utils] Ciclo de dependências detectado: {' -> '.join(pilha + [nome])}")
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
                logger.error(f"Classe '{nome}' não é instância válida de {tipo_instancia}")
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
