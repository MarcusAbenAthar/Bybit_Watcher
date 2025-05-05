"""
SchemaGenerator: Gera e versiona schemas do banco de dados conforme plugin_tabelas.
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import json
import os
import datetime
import inspect
import importlib
import pkgutil
import logging

from utils.config import SCHEMA_JSON_PATH
from utils.logging_config import log_banco
from plugins.plugin import Plugin  # classe base


@dataclass
class SchemaDiff:
    """Diferenças entre versões de schema."""

    tabelas_adicionadas: List[str]
    tabelas_removidas: List[str]
    colunas_alteradas: Dict[str, List[str]]


class SchemaGenerator:
    """Gerencia criação e migração de schemas de banco de dados."""

    def __init__(self, schema_path: str):
        self.schema_path = Path(schema_path)
        self.schema_dir = self.schema_path.parent
        self.history_dir = self.schema_dir / "schema_history"
        self.history_dir.mkdir(exist_ok=True)

    def gerar_diff(self, schema_atual: Dict, schema_novo: Dict) -> SchemaDiff:
        """Identifica diferenças entre schemas."""
        tabelas_atual = set(schema_atual.get("tabelas", {}).keys())
        tabelas_novo = set(schema_novo.get("tabelas", {}).keys())

        diff = SchemaDiff(
            tabelas_adicionadas=list(tabelas_novo - tabelas_atual),
            tabelas_removidas=list(tabelas_atual - tabelas_novo),
            colunas_alteradas=self._comparar_colunas(schema_atual, schema_novo),
        )

        log_banco(
            plugin="SCHEMA_GENERATOR",
            tabela="ALL",
            operacao="SCHEMA_DIFF",
            dados=f"Diff gerado: {len(diff.tabelas_adicionadas)} adições, {len(diff.tabelas_removidas)} remoções",
            nivel=logging.INFO,
        )
        return diff

    def _comparar_colunas(
        self, schema_atual: Dict, schema_novo: Dict
    ) -> Dict[str, List[str]]:
        """Compara colunas de tabelas existentes."""
        alteracoes = {}
        for tabela in set(schema_atual["tabelas"]) & set(schema_novo["tabelas"]):
            colunas_atual = set(
                schema_atual["tabelas"][tabela].get("columns", {}).keys()
            )
            colunas_novo = set(schema_novo["tabelas"][tabela].get("columns", {}).keys())

            diff = list(colunas_novo - colunas_atual)
            if diff:
                alteracoes[tabela] = diff
        return alteracoes

    def criar_backup(self, schema: Dict) -> None:
        """Cria snapshot do schema atual."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.history_dir / f"schema_backup_{timestamp}.json"

        with backup_path.open("w") as f:
            json.dump(schema, f, indent=2)

        log_banco(
            plugin="SCHEMA_GENERATOR",
            tabela="ALL",
            operacao="SCHEMA_BACKUP",
            dados=f"Backup criado: {backup_path}",
            nivel=logging.INFO,
        )

    def gerar_script_migracao(self, diff: SchemaDiff) -> List[str]:
        """Gera comandos SQL para migração."""
        comandos = []

        # Comandos para novas tabelas
        for tabela in diff.tabelas_adicionadas:
            comandos.append(f"CREATE TABLE {tabela} (id SERIAL PRIMARY KEY);")

        # Comandos para novas colunas
        for tabela, colunas in diff.colunas_alteradas.items():
            for coluna in colunas:
                # Tipo padrão
                comandos.append(f"ALTER TABLE {tabela} ADD COLUMN {coluna} VARCHAR;")

        log_banco(
            plugin="SCHEMA_GENERATOR",
            tabela="ALL",
            operacao="MIGRATION_SCRIPT",
            dados=f"Script gerado com {len(comandos)} comandos",
            nivel=logging.INFO,
        )
        return comandos


def validar_plugin_tabelas(plugin) -> bool:
    """
    Valida a estrutura plugin_tabelas de um plugin.

    Args:
        plugin: Instância do plugin a validar

    Returns:
        bool: True se válido, False caso contrário
    """
    if not hasattr(plugin, "plugin_tabelas"):
        return False

    required_keys = {"schema", "modo_acesso"}
    for tabela, config in plugin.plugin_tabelas.items():
        if not required_keys.issubset(config.keys()):
            return False

    return True


class MockGerente:
    """Mock do gerenciador para geração de schema"""

    def __init__(self):
        pass


class MockConexao:
    """Mock da conexão para geração de schema"""

    def __init__(self):
        pass


def generate_schema():
    """Gera ou atualiza o arquivo schema.json com campos consolidados."""
    # Estrutura inicial do JSON
    schema = {
        "schema_versao": "1.0",
        "gerado_por": "gerenciador_banco",
        "tabelas": {
            "dados": {
                "columns": {
                    "timestamp": "FLOAT",
                    "symbol": "VARCHAR(20)",
                    "price": "FLOAT",
                },
                "plugin": "system",
            }
        },
    }

    # Cria instâncias mock para dependências
    mock_gerente = MockGerente()
    mock_conexao = MockConexao()

    # Varre todos os submódulos em plugins/
    import plugins

    pkg = plugins
    for finder, modname, ispkg in pkgutil.walk_packages(
        pkg.__path__, pkg.__name__ + "."
    ):
        try:
            mod = importlib.import_module(modname)
        except Exception as e:
            logging.warning(f"[SchemaGenerator] falha ao importar {modname}: {e}")
            continue

        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if not issubclass(cls, Plugin) or cls is Plugin:
                continue

            try:
                # Instancia o plugin com mocks necessários
                kwargs = {}
                if "gerente" in inspect.signature(cls).parameters:
                    kwargs["gerente"] = None
                plugin = cls(**kwargs)
                if hasattr(plugin, "plugin_tabelas"):
                    tabelas = plugin.plugin_tabelas
                    for nome_tabela, conf in tabelas.items():
                        # Aceita tanto 'schema' (padrão novo) quanto 'columns' (retrocompatibilidade)
                        columns = conf.get("schema") or conf.get("columns", {})
                        # Corrigir columns aninhado
                        if (
                            isinstance(columns, dict)
                            and "columns" in columns
                            and isinstance(columns["columns"], dict)
                        ):
                            columns = columns["columns"]
                        if not columns or not isinstance(columns, dict):
                            logging.warning(
                                f"[SchemaGenerator] Tabela '{nome_tabela}' do plugin '{plugin.PLUGIN_NAME}' ignorada: columns inválido ou vazio."
                            )
                            continue
                        schema["tabelas"][nome_tabela] = {
                            "columns": columns,
                            "plugin": plugin.PLUGIN_NAME,
                            "schema_versao": getattr(
                                plugin, "plugin_schema_versao", "1.0"
                            ),
                        }
            except Exception as e:
                logging.warning(
                    f"[SchemaGenerator] Falha ao processar plugin {cls}: {e}"
                )
                continue

    # Garante que o schema.json será salvo em utils/schema.json
    path = Path(SCHEMA_JSON_PATH)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = str(Path(SCHEMA_JSON_PATH).absolute())

    # Solução definitiva para BOM
    # Força recriação se existir com BOM
    if os.path.exists(schema_path):
        try:
            with open(schema_path, "rb") as f:
                if f.read(3) == b"\xef\xbb\xbf":  # Detecta BOM
                    os.remove(schema_path)  # Deleta arquivo com BOM
        except:
            pass

    # Sempre cria novo arquivo sem BOM
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(
        f"[SchemaGenerator] schema atualizado em {datetime.datetime.now().isoformat()} → {path}"
    )


class SchemaGenerator:
    def __init__(self):
        self._tipos_validos = {
            "INTEGER",
            "VARCHAR",
            "DECIMAL",
            "TIMESTAMP",
            "BOOLEAN",
            "SERIAL",
        }

    def validar_tipo_coluna(self, tipo: str) -> bool:
        """Valida se um tipo SQL é suportado."""
        return tipo.split("(")[0].upper() in self._tipos_validos
