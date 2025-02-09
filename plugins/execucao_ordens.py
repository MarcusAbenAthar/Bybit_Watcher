import logging
from utils.singleton import singleton
from plugins.plugin import Plugin
from plugins.gerente_plugin import GerentePlugin

logger = logging.getLogger(__name__)


@singleton
class ExecucaoOrdens(Plugin):
    """Plugin para execução de ordens de trading."""

    def __init__(self):
        """Inicializa o plugin ExecucaoOrdens."""
        super().__init__()
        self.nome = "Execução de Ordens"
        self.descricao = "Plugin para execução de ordens de trading"
        self._config = None
        self.gerente = GerentePlugin()
        self._ordens_pendentes = {}

    def inicializar(self, config):
        """
        Inicializa o plugin com as configurações fornecidas.

        Args:
            config: Objeto de configuração
        """
        if not self._config:  # Só inicializa uma vez
            super().inicializar(config)
            self._config = config
            self._ordens_pendentes = {}
            logger.info(f"Plugin {self.nome} inicializado com sucesso")

    def exibir_sinal(self, sinal):
        """
        Exibe os detalhes do sinal de trading de forma organizada.

        Args:
            sinal (dict): Um dicionário com os detalhes do sinal, incluindo o symbol de moedas,
                         o timeframe, o tipo de sinal (compra ou venda), o stop loss e o take profit.
        """
        if sinal["sinal"]:
            mensagem = f"""
            Sinal: {sinal['sinal']}
            Par: {sinal['symbol']}
            Timeframe: {sinal['timeframe']}
            Stop Loss: {sinal['stop_loss']:.2f}
            Take Profit: {sinal['take_profit']:.2f}
            """
            logger.info(mensagem)  # Usando logger para exibir o sinal

    def executar(self, dados, symbol, timeframe):
        """
        Executa as ordens.

        Args:
            dados (list): Dados para análise
            symbol (str): Símbolo do par
            timeframe (str): Timeframe dos dados
        """
        try:
            # Implementação da execução
            return self.executar_ordem(dados)
        except Exception as e:
            logger.error(f"Erro ao executar ordem: {e}")
            raise

    def executar_ordem(self, dados):
        """
        Executa uma ordem de compra/venda.

        Args:
            dados (dict): Dados da ordem a ser executada
        """
        try:
            # Mudando de INFO para DEBUG já que são detalhes de execução
            logger.debug(f"Executando ordem: {dados}")

            # Aqui você pode implementar a lógica de execução de ordens
            return True

        except Exception as e:
            logger.error(f"Erro ao executar ordem: {e}")
            raise
