class Plugin:
    """Classe base para plugins."""

    def __init__(self):
        self.nome = "Plugin Base"
        self.descricao = "Classe base para plugins"
        self._config = None
        self.gerente = None

    def inicializar(self, config):
        """Inicializa o plugin com configurações."""
        self._config = config
        return True

    def obter_pares_usdt(self):
        """Método base para obter pares USDT."""
        raise NotImplementedError("Método obter_pares_usdt não implementado")

    def executar(self, dados, symbol, timeframe):
        """
        Executa a lógica principal do plugin.

        Este método é chamado pelo bot a cada iteração do loop principal.
        Plugins devem implementar a lógica de processamento de dados,
        geração de sinais, etc. neste método.

        Args:
            dados (list): Os dados de mercado (klines).
            symbol (str): O symbol de criptomoedas.
            timeframe (str): O timeframe dos dados.
        """
        pass  # Implementação padrão (sem ação)

    def finalizar(self):
        """
        Finaliza o plugin.

        Este método é chamado pelo bot após o loop principal.
        Plugins podem usar este método para liberar recursos,
        salvar dados, etc.
        """
        pass  # Implementação padrão (sem ação)
