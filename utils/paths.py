# utils/paths.py
import os


def get_root_gerenciadores():
    # Corrigido para acessar a raiz do projeto
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def get_root_plugins():
    # Aqui estamos no diretório plugins, então podemos pegar ele mesmo
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_schema_path():
    # Acessando o schema.json a partir da raiz do projeto
    return os.path.join(get_root_gerenciadores(), "utils", "schema.json")
