# gerenciador_monitoramento.py
"""
GerenciadorMonitoramento
-----------------------
Gerencia todos os plugins de monitoramento (funding, open interest, onchain, etc) de forma modular, segura e padronizada.
Herdado de BaseGerenciador. Descobre e inicializa plugins dinamicamente da pasta monitoramento.

Regras:
- Responsabilidade única: orquestrar plugins de monitoramento.
- Modular, testável, seguro, documentado.
- Interface padronizada: inicializar, executar, coletar diagnósticos.
- Autoidentificação de plugins monitorados.
"""
import importlib
import pkgutil
import os
from typing import Dict, Any, List
from plugins.gerenciadores.gerenciador import BaseGerenciador
from utils.logging_config import get_logger

logger = get_logger(__name__)

class GerenciadorMonitoramento(BaseGerenciador):
    """
    Gerenciador de monitoramento de mercado e execução de plugins de monitoramento.
    - Responsabilidade única: orquestração de plugins de monitoramento e análise de mercado.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/gerenciadores.
    """
    PLUGIN_NAME = "gerenciador_monitoramento"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["monitoramento", "mercado", "orquestrador"]
    PLUGIN_PRIORIDADE = 10

    def finalizar(self) -> bool:
        """
        Finaliza o gerenciador de monitoramento, encerrando todos os plugins monitorados.
        Limpa configurações, plugins e marca como não inicializado.
        Retorna:
            bool: True se finalizado com sucesso, False caso contrário.
        """
        try:
            for nome, plugin in self._plugins.items():
                try:
                    if hasattr(plugin, 'finalizar'):
                        plugin.finalizar()
                    logger.info(f"Plugin monitoramento finalizado: {nome}")
                except Exception as e:
                    logger.error(f"Erro ao finalizar plugin monitoramento {nome}: {e}")
            self._plugins.clear()
            self._config = {}
            self.inicializado = False
            super().finalizar()
            logger.info("GerenciadorMonitoramento finalizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao finalizar GerenciadorMonitoramento: {e}")
            return False

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do GerenciadorMonitoramento.
        """
        return []

    @classmethod
    def identificar_plugins(cls):
        """
        Retorna o nome do gerenciador para autoidentificação.
        """
        return cls.PLUGIN_NAME

    PLUGIN_NAME = "gerenciador_monitoramento"

    def __init__(self, config=None):
        super().__init__()
        self._config = config or {}
        self._plugins: Dict[str, Any] = {}
        self.inicializado = False

    def inicializar(self, config: dict = None):
        """
        Inicializa todos os plugins de monitoramento disponíveis na pasta monitoramento.
        """
        if self.inicializado:
            logger.info("[GerenciadorMonitoramento] Já inicializado.")
            return
        self._config = config or self._config
        self._plugins = self._descobrir_plugins_monitoramento()
        self.inicializado = True
        logger.info(f"[GerenciadorMonitoramento] Inicializado com {len(self._plugins)} plugins.")

    def executar(self, *args, **kwargs) -> Dict[str, dict]:
        """
        Executa todos os diagnósticos dos plugins de monitoramento.
        Retorna um dicionário {nome_plugin: diagnostico}
        """
        resultados = {}
        for nome, plugin in self._plugins.items():
            try:
                import inspect
                sig = inspect.signature(plugin.diagnostico)
                params = sig.parameters
                # Monta kwargs apenas com argumentos aceitos
                call_kwargs = {}
                for p in params:
                    if p in kwargs:
                        call_kwargs[p] = kwargs[p]
                resultado = plugin.diagnostico(**call_kwargs)
                resultados[nome] = resultado
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Erro ao executar {nome}: {e}")
                resultados[nome] = {"status": "ERRO", "erro": str(e)}
        return resultados

    def monitorar_continuamente(self, intervalo_segundos: int = 60, *args, **kwargs):
        """
        Executa todos os diagnósticos dos plugins de monitoramento em loop contínuo institucional.
        Args:
            intervalo_segundos (int): Intervalo entre execuções em segundos.
        """
        import time
        logger.info(f"[GerenciadorMonitoramento] Monitoramento contínuo iniciado (intervalo: {intervalo_segundos}s)")
        try:
            while True:
                resultados = self.executar(*args, **kwargs)
                logger.info(f"[GerenciadorMonitoramento] Diagnóstico: {resultados}")
                time.sleep(intervalo_segundos)
        except KeyboardInterrupt:
            logger.info("[GerenciadorMonitoramento] Monitoramento contínuo interrompido pelo usuário.")
        except Exception as e:
            logger.error(f"[GerenciadorMonitoramento] Erro no loop de monitoramento: {e}")

        return resultados

    def listar_plugins(self) -> List[str]:
        """
        Lista todos os plugins de monitoramento carregados.
        """
        return list(self._plugins.keys())

    def _descobrir_plugins_monitoramento(self) -> Dict[str, Any]:
        """
        Descobre, resolve dependências e instancia todos os plugins na pasta monitoramento.
        Faz auto plug-in, auto injeção e detecção de dependências, com logs e validação de ciclos.
        """
        plugins = {}
        pacote = 'plugins.monitoramento'
        diretorio = os.path.join(os.path.dirname(__file__), '..', 'monitoramento')
        registry = {}  # Para instâncias já criadas
        grafo_dependencias = {}

        # 1. Descoberta de classes de plugins
        classes_plugins = {}
        for _, nome_modulo, is_pkg in pkgutil.iter_modules([diretorio]):
            if is_pkg or nome_modulo.startswith('__'):
                continue
            try:
                modulo = importlib.import_module(f'{pacote}.{nome_modulo}')
                for atributo in dir(modulo):
                    obj = getattr(modulo, atributo)
                    if isinstance(obj, type) and hasattr(obj, 'diagnostico') and hasattr(obj, 'PLUGIN_NAME'):
                        classes_plugins[obj.PLUGIN_NAME] = obj
                        logger.info(f"[GerenciadorMonitoramento] Classe plugin {obj.PLUGIN_NAME} descoberta.")
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Falha ao importar {nome_modulo}: {e}")

        # 2. Monta grafo de dependências
        for nome, cls in classes_plugins.items():
            try:
                deps = cls.dependencias() if hasattr(cls, 'dependencias') else []
                grafo_dependencias[nome] = deps
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Erro ao consultar dependências de {nome}: {e}")
                grafo_dependencias[nome] = []

        # 3. Resolve dependências e instancia plugins
        def resolver_plugin(nome, pilha=None):
            if nome in registry:
                return registry[nome]
            pilha = pilha or []
            if nome in pilha:
                logger.error(f"[GerenciadorMonitoramento] Ciclo de dependências detectado: {' -> '.join(pilha + [nome])}")
                raise RuntimeError(f"Ciclo de dependências: {' -> '.join(pilha + [nome])}")
            pilha.append(nome)
            cls = classes_plugins[nome]
            deps = grafo_dependencias.get(nome, [])
            kwargs = {}
            for dep in deps:
                if dep in classes_plugins:
                    kwargs[dep] = resolver_plugin(dep, pilha=list(pilha))
                else:
                    logger.warning(f"[GerenciadorMonitoramento] Dependência {dep} de {nome} não encontrada entre plugins.")
            try:
                instancia = cls(**kwargs) if kwargs else cls()
                registry[nome] = instancia
                logger.info(f"[GerenciadorMonitoramento] Plugin {nome} instanciado com deps: {list(kwargs.keys())}")
                return instancia
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Falha ao instanciar {nome}: {e}")
                raise
        # Instancia todos, resolvendo dependências recursivamente
        for nome in classes_plugins:
            try:
                plugins[nome] = resolver_plugin(nome)
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Plugin {nome} não carregado: {e}")
        return plugins

        """
        Descobre, resolve dependências e instancia todos os plugins na pasta monitoramento.
        Faz auto plug-in, auto injeção e detecção de dependências, com logs e validação de ciclos.
        """
        plugins = {}
        pacote = 'plugins.monitoramento'
        diretorio = os.path.join(os.path.dirname(__file__), '..', 'monitoramento')
        registry = {}  # Para instâncias já criadas
        dependencias_pendentes = {}  # {plugin_name: [deps]}
        grafo_dependencias = {}  # Para detecção de ciclos

        # 1. Descoberta de classes de plugins
        classes_plugins = {}
        for _, nome_modulo, is_pkg in pkgutil.iter_modules([diretorio]):
            if is_pkg or nome_modulo.startswith('__'):
                continue
            try:
                modulo = importlib.import_module(f'{pacote}.{nome_modulo}')
                for atributo in dir(modulo):
                    obj = getattr(modulo, atributo)
                    if isinstance(obj, type) and hasattr(obj, 'diagnostico') and hasattr(obj, 'PLUGIN_NAME'):
                        classes_plugins[obj.PLUGIN_NAME] = obj
                        logger.info(f"[GerenciadorMonitoramento] Classe plugin {obj.PLUGIN_NAME} descoberta.")
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Falha ao importar {nome_modulo}: {e}")

        # 2. Monta grafo de dependências
        for nome, cls in classes_plugins.items():
            try:
                deps = cls.dependencias() if hasattr(cls, 'dependencias') else []
                grafo_dependencias[nome] = deps
                dependencias_pendentes[nome] = list(deps)
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Erro ao consultar dependências de {nome}: {e}")
                dependencias_pendentes[nome] = []

        # 3. Resolve dependências e instancia plugins
        def resolver_plugin(nome, pilha=None):
            if nome in registry:
                return registry[nome]
            pilha = pilha or []
            if nome in pilha:
                logger.error(f"[GerenciadorMonitoramento] Ciclo de dependências detectado: {' -> '.join(pilha + [nome])}")
                raise RuntimeError(f"Ciclo de dependências: {' -> '.join(pilha + [nome])}")
            pilha.append(nome)
            cls = classes_plugins[nome]
            deps = grafo_dependencias.get(nome, [])
            kwargs = {}
            for dep in deps:
                if dep in classes_plugins:
                    kwargs[dep] = resolver_plugin(dep, pilha=list(pilha))
                else:
                    logger.warning(f"[GerenciadorMonitoramento] Dependência {dep} de {nome} não encontrada entre plugins.")
            try:
                instancia = cls(**kwargs) if kwargs else cls()
                registry[nome] = instancia
                logger.info(f"[GerenciadorMonitoramento] Plugin {nome} instanciado com deps: {list(kwargs.keys())}")
                return instancia
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Falha ao instanciar {nome}: {e}")
                raise
        # Instancia todos, resolvendo dependências recursivamente
        for nome in classes_plugins:
            try:
                plugins[nome] = resolver_plugin(nome)
            except Exception as e:
                logger.error(f"[GerenciadorMonitoramento] Plugin {nome} não carregado: {e}")
        return plugins

    @classmethod
    def dependencias(cls):
        """Autoidentificação das dependências do gerenciador."""
        return []

    @classmethod
    def identificar_plugins(cls):
        """Autoidentificação do gerenciador."""
        return cls.PLUGIN_NAME
