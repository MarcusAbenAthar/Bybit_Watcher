from trading_core import Core
from plugins.plugin import Plugin
from venv import logger  # Certifique-se de ter o logger configurado corretamente


class ExecucaoOrdens(Plugin):
    """
    Plugin para executar as ordens de compra e venda, agora integrado com o Core.
    """

    def __init__(self, core: Core):  # Agora recebe o Core na inicialização
        self.core = core
        super().__init__(
            self.core.config
        )  # Inicializa a classe Plugin com as configurações do Core
        self.conexao = self.core.conexao  # Obtém a conexão com a exchange do Core

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
        Recebe e executa o sinal de trading, utilizando a conexão com a exchange do Core.

        Args:
            sinal (dict): Um dicionário com os detalhes do sinal.
        """
        self.exibir_sinal(sinal)

        if sinal["sinal"] == "COMPRA":  # Adapte conforme a estrutura do seu sinal
            try:
                order = self.conexao.obter_exchange().create_order(  # Utilize a conexão do Core
                    symbol=sinal["par"],
                    type="market",  # Ou o tipo de ordem desejado
                    side="buy",
                    amount=0.01,  # Ajuste a quantidade conforme necessário
                    params={
                        "stopLoss": sinal["stop_loss"],
                        "takeProfit": sinal["take_profit"],
                    },  # Adapte conforme a API da exchange
                )
                logger.info(f"Ordem de compra executada: {order}")
            except Exception as e:
                logger.error(f"Erro ao executar ordem de compra: {e}")
        elif sinal["sinal"] == "VENDA":  # Adapte conforme a estrutura do seu sinal
            try:
                order = self.conexao.obter_exchange().create_order(  # Utilize a conexão do Core
                    symbol=sinal["par"],
                    type="market",  # Ou o tipo de ordem desejado
                    side="sell",
                    amount=0.01,  # Ajuste a quantidade conforme necessário
                    params={
                        "stopLoss": sinal["stop_loss"],
                        "takeProfit": sinal["take_profit"],
                    },  # Adapte conforme a API da exchange
                )
                logger.info(f"Ordem de venda executada: {order}")
            except Exception as e:
                logger.error(f"Erro ao executar ordem de venda: {e}")
        else:
            logger.warning(f"Sinal inválido: {sinal['sinal']}")
