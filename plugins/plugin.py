from loguru import logger


class Plugin:
    """Classe base para plugins."""

    def __init__(self):
        self.nome = None  # Deve ser definido nas subclasses
        self.descricao = None  # Deve ser definido nas subclasses
        self.inicializado = False
        self._config = None
        self.gerente = None

    def inicializar(self, config: dict) -> bool:
        """Inicializa o plugin."""
        try:
            self._config = config
            self.inicializado = True
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar {self.nome}: {e}")
            return False

    def obter_pares_usdt(self):
        """Método base para obter pares USDT."""
        raise NotImplementedError("Método obter_pares_usdt não implementado")

    def executar(self) -> bool:
        """Executa o ciclo do plugin."""
        return True

    def finalizar(self):
        """Finaliza o plugin."""
        pass
