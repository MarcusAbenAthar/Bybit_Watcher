"""
SchemaGenerator: varre plugins, extrai INPUT_FIELDS/OUTPUT_FIELDS
    e mantém um schema.json atualizado, incluindo timestamp de geração.
"""
import pkgutil
import importlib
import inspect
import json
from datetime import datetime
from pathlib import Path

from utils.config import SCHEMA_JSON_PATH
from plugins.plugin import Plugin  # classe base
from utils.logging_config import get_logger
logger = get_logger(__name__)

def generate_schema():
    """Gera ou atualiza o arquivo schema.json com campos consolidados."""
    # Estrutura inicial do JSON
    schema = {
        "generated_at": datetime.now().isoformat() + "Z",
        "columns": {}
    }

    # Varre todos os submódulos em plugins/
    import plugins
    pkg = plugins
    for finder, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            mod = importlib.import_module(modname)
        except Exception as e:
            logger.warning(f"[SchemaGenerator] falha ao importar {modname}: {e}")
            continue
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if not issubclass(cls, Plugin) or cls is Plugin:
                continue

            # Extrai campos declarados (INPUT_FIELDS/OUTPUT_FIELDS)
            inputs = getattr(cls, "INPUT_FIELDS", [])
            outputs = getattr(cls, "OUTPUT_FIELDS", [])
            for fld in inputs + outputs:
                schema["columns"].setdefault(fld, "FLOAT")

    # Compara e atualiza somente se mudou
    # Garante que o schema.json será salvo em utils/schema.json
    path = Path(SCHEMA_JSON_PATH)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("columns") == schema["columns"]:
            return  # nada mudou

    # Escreve novo schema.json sempre em utils/
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    print(f"[SchemaGenerator] schema atualizado em {schema['generated_at']} → {path}")
