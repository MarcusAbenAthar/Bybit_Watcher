# plugins/plugin.py


class Plugin:
    """
    Classe base para todos os plugins do bot.

    Define os métodos básicos que todos os plugins devem implementar:
    - inicializar(): Inicializa o plugin.
    - executar(): Executa a lógica principal do plugin.
    - finalizar(): Finaliza o plugin.
    """

    def __init__(self, config):
        """
        Inicializa o plugin.

        Args:
            config (dict): Um dicionário com as configurações do bot.
        """
        self.config = config

    def inicializar(self, plugins=None):
        """
        Inicializa o plugin.

        Este método é chamado pelo bot antes do loop principal.
        Plugins podem usar este método para configurar recursos,
        carregar dados, etc.
        """
        pass  # Implementação padrão (sem ação)

    def executar(self, dados, par, timeframe):
        """
        Executa a lógica principal do plugin.

        Este método é chamado pelo bot a cada iteração do loop principal.
        Plugins devem implementar a lógica de processamento de dados,
        geração de sinais, etc. neste método.

        Args:
            dados (list): Os dados de mercado (klines).
            par (str): O par de criptomoedas.
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
