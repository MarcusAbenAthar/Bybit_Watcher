from core import Core
from plugins.plugin import Plugin


class ExecucaoOrdens(Plugin):
    """
    Plugin para executar as ordens de compra e venda.
    """

    def __init__(self, container: AppModule):
        self.container = container
        super().__init__(container.config())


def exibir_sinal(self, sinal):
    """
    Exibe os detalhes do sinal de trading de forma organizada.

    Args:
        sinal (dict): Um dicionário com os detalhes do sinal, incluindo o par de moedas, o timeframe, o tipo de sinal (compra ou venda), o stop loss e o take profit.
    """
    if sinal["sinal"]:
        mensagem = f"""
        Sinal: {sinal['sinal']}
        Par: {sinal['par']}
        Timeframe: {sinal['timeframe']}
        Stop Loss: {sinal['stop_loss']:.2f}
        Take Profit: {sinal['take_profit']:.2f}
        """
        print(mensagem)


def executar(self, sinal):
    """
    Recebe e exibe o sinal de trading.

    Args:
        sinal (dict): Um dicionário com os detalhes do sinal.
    """
    self.exibir_sinal(sinal)
