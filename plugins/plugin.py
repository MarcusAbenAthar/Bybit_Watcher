# plugins/plugin.py
class Plugin:
    """
    Classe base para plugins.

    Atributos de Classe:
        PLUGIN_NAME (str): Nome do plugin (deve ser sobrescrito)
        PLUGIN_TYPE (str): Tipo do plugin (essencial ou adicional)
    """

    PLUGIN_NAME = None  # Deve ser definido nas subclasses
    PLUGIN_TYPE = None  # Deve ser definido nas subclasses

    def __init__(self):
        """Inicializa o plugin com valores padrão."""
        if not hasattr(self, "_nome"):
            self._nome = self.PLUGIN_NAME if self.PLUGIN_NAME else ""
        if not hasattr(self, "descricao"):
            self.descricao = ""
        if not hasattr(self, "tipo"):
            self.tipo = self.PLUGIN_TYPE if self.PLUGIN_TYPE else ""
        if not hasattr(self, "inicializado"):
            self.inicializado = False

    @property
    def nome(self):
        """Nome do plugin."""
        if hasattr(self, "_nome"):
            return self._nome
        return self.PLUGIN_NAME if self.PLUGIN_NAME else ""

    @nome.setter
    def nome(self, valor):
        """Define o nome do plugin."""
        self._nome = valor
        if not self.PLUGIN_NAME:
            self.PLUGIN_NAME = valor

    def inicializar(self, config: dict) -> bool:
        """Inicializa o plugin."""
        return True

    def executar(self) -> bool:
        """Executa o ciclo do plugin."""
        return True

    def finalizar(self):
        """Finaliza o plugin."""
        pass
