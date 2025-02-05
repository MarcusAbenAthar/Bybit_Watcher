from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_conexao
from loguru import logger


class ExecucaoOrdens(Plugin):
    """
    Plugin para exibir sinais de trading.

    Este plugin é responsável por receber sinais de trading gerados por outros plugins
    e exibi-los de forma organizada no console.
    """

    def __init__(self):
        """Inicializa o plugin ExecucaoOrdens."""
        super().__init__()
        self.conexao = obter_conexao()

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

    def executar(self, sinal):
        """
        Recebe e exibe o sinal de trading.

        Args:
            sinal (dict): Um dicionário com os detalhes do sinal.
        """
        self.exibir_sinal(sinal)
