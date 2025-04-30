import json
import os
import inspect
from collections import defaultdict, deque
from typing import Optional, List
from plugins.plugin import Plugin, PluginRegistry
from plugins.gerenciadores.gerenciador import BaseGerenciador
from utils.logging_config import get_logger

logger = get_logger(__name__)

ARQUIVO_DEPENDENCIAS = os.path.join("utils", "plugins_dependencias.json")


class GerenciadorPlugins(BaseGerenciador):
    """Gerenciador responsável por carregar, inicializar e coordenar plugins do sistema."""

    PLUGIN_NAME = "gerenciador_plugins"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["core"]

    def __init__(self, **kwargs):
        """Inicializa o gerenciador de plugins com suporte à classe base."""
        super().__init__(**kwargs)
        self.plugins: dict[str, Plugin] = {}
        self._config: dict = {}
        self._dependencias: dict[str, list[str]] = {}

    def _registrar_gerenciadores(self):
        """Instancia e registra automaticamente os gerenciadores conhecidos."""
        for nome, cls in BaseGerenciador.listar_gerenciadores().items():
            try:
                instancia = cls()
                self.plugins[nome] = instancia
                logger.debug(f"Gerenciador registrado: {nome}")
            except Exception as e:
                logger.error(f"Erro ao registrar gerenciador '{nome}': {e}")
        logger.debug(f"Gerenciadores disponíveis após registro: {list(self.plugins.keys())}")

    def _coletar_dependencias_reais(self) -> dict[str, list[str]]:
        """Inspeciona os __init__ dos plugins para descobrir dependências, incluindo gerenciadores."""
        dependencias = {}
        gerenciadores_registrados = {
            nome: cls for nome, cls in BaseGerenciador.listar_gerenciadores().items()
        }

        for nome_plugin, cls in PluginRegistry.todos().items():
            sig = inspect.signature(cls.__init__)
            deps = []
            for param in list(sig.parameters.values())[1:]:  # Ignora 'self'
                if param.name in {"gerente", "args", "kwargs"} or param.name.startswith(
                    "_"
                ):
                    continue

                anotacao = param.annotation
                if (
                    inspect.isclass(anotacao)
                    and issubclass(anotacao, BaseGerenciador)
                    and hasattr(anotacao, "PLUGIN_NAME")
                ):
                    gerenciador_nome = getattr(anotacao, "PLUGIN_NAME", param.name)
                    if gerenciador_nome in gerenciadores_registrados:
                        deps.append(gerenciador_nome)
                        continue

                deps.append(param.name)
            dependencias[nome_plugin] = deps
        return dependencias

    def _carregar_dependencias_json(self) -> dict[str, list[str]]:
        """Carrega dependências de plugins a partir de um arquivo JSON."""
        if os.path.exists(ARQUIVO_DEPENDENCIAS):
            try:
                with open(ARQUIVO_DEPENDENCIAS, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar {ARQUIVO_DEPENDENCIAS}: {e}")
        return {}

    def _salvar_dependencias_json(self, dependencias: dict[str, list[str]]) -> None:
        """Salva as dependências dos plugins em um arquivo JSON."""
        try:
            with open(ARQUIVO_DEPENDENCIAS, "w") as f:
                json.dump(dependencias, f, indent=4)
            logger.info(f"{ARQUIVO_DEPENDENCIAS} atualizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar {ARQUIVO_DEPENDENCIAS}: {e}")

    def _verificar_ou_atualizar_dependencias(self) -> None:
        """Compara dependências reais com as salvas e atualiza o JSON se necessário."""
        declaradas = self._coletar_dependencias_reais()
        salvas = self._carregar_dependencias_json()

        if declaradas != salvas:
            logger.info("Diferenças detectadas nas dependências. Atualizando JSON...")
            self._salvar_dependencias_json(declaradas)
        else:
            logger.debug("Dependências do JSON estão atualizadas.")

        self._dependencias = declaradas

    def _ordenar_por_dependencias(self) -> list[tuple[str, type]]:
        """Ordena plugins em ordem topológica com base nas dependências."""
        grafo = defaultdict(set)
        inverso = defaultdict(set)
        todos = PluginRegistry.todos()

        for plugin, deps in self._dependencias.items():
            for dep in deps:
                grafo[dep].add(plugin)
                inverso[plugin].add(dep)

        fila = deque([p for p in todos if not inverso[p]])
        visitados = set()
        ordenados = []

        while fila:
            atual = fila.popleft()
            if atual in visitados:
                continue
            visitados.add(atual)
            ordenados.append((atual, todos[atual]))
            for vizinho in grafo[atual]:
                inverso[vizinho].remove(atual)
                if not inverso[vizinho]:
                    fila.append(vizinho)

        faltantes = set(todos) - set(a for a, _ in ordenados)
        for faltante in faltantes:
            ordenados.append((faltante, todos[faltante]))
        return ordenados

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa todos os plugins do sistema usando auto plug-in, auto injeção e detecção de dependências.
        - Descobre plugins dinamicamente.
        - Resolve dependências recursivamente via dependencias().
        - Injeta instâncias já criadas ou inicializa sob demanda.
        - Detecta ciclos e gera logs claros.
        """
        self._config = config
        self._registrar_gerenciadores()
        self._verificar_ou_atualizar_dependencias()
        sucesso = True
        registry = {}  # Plugins já instanciados
        plugins_ordenados = self._ordenar_por_dependencias()
        plugins_ordenados = [(nome, cls) for nome, cls in plugins_ordenados]
        grafo_dependencias = {nome: self._dependencias.get(nome, []) for nome, _ in plugins_ordenados}

        def resolver_plugin(nome, pilha=None):
            if nome in registry:
                return registry[nome]
            pilha = pilha or []
            if nome in pilha:
                logger.error(f"[GerenciadorPlugins] Ciclo de dependências detectado: {' -> '.join(pilha + [nome])}")
                raise RuntimeError(f"Ciclo de dependências: {' -> '.join(pilha + [nome])}")
            pilha.append(nome)
            classe = PluginRegistry.obter_plugin(nome)
            if not classe:
                # Tenta buscar como gerenciador se não for plugin
                classe = BaseGerenciador.obter_gerenciador(nome)
                if not classe:
                    logger.error(f"[GerenciadorPlugins] Plugin ou Gerenciador '{nome}' não encontrado no registro.")
                    raise RuntimeError(f"Plugin ou Gerenciador '{nome}' não encontrado.")
            deps = grafo_dependencias.get(nome, [])
            kwargs = {"gerente": self}
            for dep in deps:
                try:
                    kwargs[dep] = resolver_plugin(dep, pilha=list(pilha))
                except Exception as e:
                    logger.error(f"[GerenciadorPlugins] Falha ao resolver dependência '{dep}' para '{nome}': {e}")
                    raise
            try:
                plugin = classe(**kwargs)
                if not isinstance(plugin, (Plugin, BaseGerenciador)):
                    logger.error(f"Plugin '{nome}' não é uma instância válida de Plugin ou BaseGerenciador")
                    raise TypeError(f"Plugin '{nome}' inválido.")
                if plugin.inicializar(config):
                    registry[nome] = plugin
                    self.plugins[nome] = plugin
                    logger.info(f"Plugin carregado: {nome}")
                    return plugin
                else:
                    logger.error(f"Falha ao inicializar plugin: {nome}")
                    raise RuntimeError(f"Falha ao inicializar plugin: {nome}")
            except Exception as e:
                logger.error(f"Erro ao instanciar plugin {nome}: {e}", exc_info=True)
                raise

        # Instancia todos os plugins em ordem topológica, resolvendo dependências recursivamente
        for nome_plugin, _ in plugins_ordenados:
            try:
                resolver_plugin(nome_plugin)
            except Exception as e:
                logger.error(f"[GerenciadorPlugins] Plugin {nome_plugin} não carregado: {e}")
                sucesso = False
        self.inicializado = sucesso
        return sucesso

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa plugins com a tag 'analise' em sequência.

        Args:
            *args: Argumentos posicionais para os plugins
            **kwargs: Argumentos nomeados para os plugins (ex.: symbol, timeframe)

        Returns:
            bool: True se todos os plugins forem executados com sucesso, False caso contrário
        """
        if not self.inicializado:
            logger.error("GerenciadorPlugins não inicializado")
            return False

        try:
            plugins_analise = self.filtrar_por_tag("analise")
            if not plugins_analise:
                logger.warning("Nenhum plugin com tag 'analise' encontrado")
                return True  # Considera sucesso se não há plugins para executar

            sucesso = True
            for plugin in plugins_analise:
                try:
                    resultado = plugin.executar(*args, **kwargs)
                    if not isinstance(resultado, bool) or not resultado:
                        logger.warning(
                            f"Falha na execução do plugin {plugin.PLUGIN_NAME}"
                        )
                        sucesso = False
                except Exception as e:
                    logger.error(
                        f"Erro ao executar plugin {plugin.PLUGIN_NAME}: {e}",
                        exc_info=True,
                    )
                    sucesso = False
            return sucesso
        except Exception as e:
            logger.error(f"Erro geral na execução dos plugins: {e}", exc_info=True)
            return False

    def obter_plugin(self, nome: str) -> Optional[Plugin]:
        """Recupera um plugin pelo nome."""
        plugin = self.plugins.get(nome)
        if not plugin:
            logger.warning(f"Plugin '{nome}' não encontrado.")
        return plugin

    def filtrar_por_tag(self, tag: str) -> List[Plugin]:
        """Filtra plugins por uma tag específica."""
        return [
            plugin
            for plugin in self.plugins.values()
            if tag in getattr(plugin, "PLUGIN_TAGS", [])
        ]

    def listar_tags(self) -> dict[str, list[str]]:
        """Lista todas as tags e seus plugins associados."""
        mapa = {}
        for nome, plugin in self.plugins.items():
            for tag in getattr(plugin, "PLUGIN_TAGS", []):
                mapa.setdefault(tag, []).append(nome)
        return mapa

    def validar_arquitetura(self) -> bool:
        """Valida a arquitetura dos plugins registrados."""
        valido = True
        nomes_usados = set()

        for nome, cls in PluginRegistry.todos().items():
            if not nome:
                logger.error(f"Plugin sem PLUGIN_NAME definido: {cls}")
                valido = False
            elif nome in nomes_usados:
                logger.error(f"PLUGIN_NAME duplicado: {nome}")
                valido = False
            else:
                nomes_usados.add(nome)

            categoria = getattr(cls, "PLUGIN_CATEGORIA", None)
            if categoria not in {"plugin", "gerenciador"}:
                logger.warning(f"PLUGIN_CATEGORIA inválida ou ausente em {nome}")

            tags = getattr(cls, "PLUGIN_TAGS", [])
            if not tags:
                logger.warning(f"PLUGIN_TAGS ausente em {nome}")

        logger.info(
            "Validação da arquitetura concluída." if valido else "Validação falhou."
        )
        return valido

    def finalizar(self) -> None:
        """Finaliza todos os plugins carregados."""
        for nome, plugin in self.plugins.items():
            try:
                plugin.finalizar()
                logger.info(f"Plugin finalizado: {nome}")
            except Exception as e:
                logger.error(f"Erro ao finalizar plugin {nome}: {e}")
        self.plugins.clear()
        self.inicializado = False

    def listar_plugins_registrados(self) -> None:
        """Lista todos os plugins registrados."""
        for nome in self.plugins:
            logger.info(f"Plugin disponível: {nome}")
