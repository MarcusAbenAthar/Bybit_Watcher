import json
import os
import inspect
from collections import defaultdict, deque
from plugins.plugin import Plugin, PluginRegistry
from plugins.gerenciadores.gerenciadores import BaseGerenciador
from utils.logging_config import get_logger

logger = get_logger(__name__)

ARQUIVO_DEPENDENCIAS = os.path.join("utils", "plugins_dependencias.json")


class GerenciadorPlugins:
    PLUGIN_NAME = "gerenciador_plugins"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["core"]

    def __init__(self):
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
        if os.path.exists(ARQUIVO_DEPENDENCIAS):
            try:
                with open(ARQUIVO_DEPENDENCIAS, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar {ARQUIVO_DEPENDENCIAS}: {e}")
        return {}

    def _salvar_dependencias_json(self, dependencias: dict[str, list[str]]) -> None:
        try:
            with open(ARQUIVO_DEPENDENCIAS, "w") as f:
                json.dump(dependencias, f, indent=4)
            logger.info(f"{ARQUIVO_DEPENDENCIAS} atualizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar {ARQUIVO_DEPENDENCIAS}: {e}")

    def _verificar_ou_atualizar_dependencias(self) -> None:
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
            logger.warning(
                f"Ordem forçada para plugin com dependência não resolvida: {faltante}"
            )

        return ordenados

    def inicializar(self, config: dict) -> bool:
        self._config = config
        self._registrar_gerenciadores()
        self._verificar_ou_atualizar_dependencias()

        sucesso = True
        plugins_ordenados = self._ordenar_por_dependencias()

        for nome_plugin, classe in plugins_ordenados:
            try:
                logger.debug(f"Instanciando plugin: {nome_plugin}")
                dependencias = {}
                for dep_nome in self._dependencias.get(nome_plugin, []):
                    dependencia = self.plugins.get(dep_nome)
                    if not dependencia:
                        logger.error(
                            f"Dependência '{dep_nome}' não encontrada para '{nome_plugin}'"
                        )
                        sucesso = False
                        break
                    dependencias[dep_nome] = dependencia

                plugin = classe(gerente=self, **dependencias)
                if plugin.inicializar(config):
                    self.plugins[nome_plugin] = plugin
                    logger.info(f"Plugin carregado: {nome_plugin}")
                else:
                    logger.error(f"Falha ao inicializar plugin: {nome_plugin}")
                    sucesso = False

            except Exception as e:
                logger.error(
                    f"Erro ao instanciar plugin {nome_plugin}: {e}", exc_info=True
                )
                sucesso = False

        return sucesso

    def obter_plugin(self, nome: str) -> Plugin | None:
        plugin = self.plugins.get(nome)
        if not plugin:
            logger.warning(f"Plugin '{nome}' não encontrado.")
        return plugin

    def filtrar_por_tag(self, tag: str) -> list[Plugin]:
        return [
            plugin
            for plugin in self.plugins.values()
            if tag in getattr(plugin, "PLUGIN_TAGS", [])
        ]

    def listar_tags(self) -> dict[str, list[str]]:
        mapa = {}
        for nome, plugin in self.plugins.items():
            for tag in getattr(plugin, "PLUGIN_TAGS", []):
                mapa.setdefault(tag, []).append(nome)
        return mapa

    def validar_arquitetura(self) -> bool:
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
        for nome, plugin in self.plugins.items():
            try:
                plugin.finalizar()
                logger.info(f"Plugin finalizado: {nome}")
            except Exception as e:
                logger.error(f"Erro ao finalizar plugin {nome}: {e}")
        self.plugins.clear()
