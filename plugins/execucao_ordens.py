# execucao_ordens.py
from utils.logging_config import get_logger
from utils.config import carregar_config
from plugins.plugin import Plugin
import ccxt

logger = get_logger(__name__)


class ExecucaoOrdens(Plugin):
    """
    Plugin responsável por executar ordens de compra/venda com SL/TP,
    incluindo reentradas (DCA) e controle de posição ativa.
    """

    PLUGIN_NAME = "execucao_ordens"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["execucao", "ordens", "trading"]
    PLUGIN_PRIORIDADE = 100

    def __init__(self, conexao=None, **kwargs):
        super().__init__(**kwargs)
        self._conexao = conexao
        self._exchange = None
        self._ordens_ativas = {}
        self._config = carregar_config()

    def inicializar(self, config_dict: dict = None) -> bool:
        try:
            self._config = config_dict or self._config
            if not super().inicializar(self._config):
                return False

            if not self._conexao or not self._conexao.exchange:
                logger.error("Plugin de conexão não encontrado ou não inicializado")
                return False

            self._exchange = self._conexao.exchange
            self._exchange.set_sandbox_mode(True)
            logger.info("ExecucaoOrdens pronto (modo sandbox ativo)")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar ExecucaoOrdens: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        dados_completos = kwargs.get("dados_completos")
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")

        resultado_padrao = {
            "execucao_ordens": {"status": "NEUTRO", "ordem_id": None, "resultado": None}
        }

        if not all([dados_completos, symbol, timeframe]):
            logger.error("Parâmetros obrigatórios ausentes")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        sinal = self._extrair_sinal(dados_completos)
        if not sinal or sinal.get("direcao") == "NEUTRO":
            logger.info(f"Nenhum sinal válido detectado para {symbol}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        auto_trade = self._config.get("trading", {}).get("auto_trade", False)
        if not auto_trade:
            logger.info("Auto Trade desativado - Ordem não executada")
            dados_completos["execucao_ordens"] = {
                "status": "PRONTO",
                "ordem_id": None,
                "resultado": "Sinal válido detectado - aguardando confirmação manual",
            }
            return True

        # Verifica se já há ordem ativa (para decidir se é DCA)
        if symbol in self._ordens_ativas:
            logger.info(f"Reentrada DCA detectada para {symbol}")
            resultado = self._executar_ordem(dados_completos, symbol, sinal, dca=True)
        else:
            logger.info(f"Ordem principal sendo executada para {symbol}")
            resultado = self._executar_ordem(dados_completos, symbol, sinal)

        dados_completos["execucao_ordens"] = resultado
        return True

    def _extrair_sinal(self, dados_completos: dict) -> dict:
        return dados_completos.get("sinais", {})

    def _executar_ordem(self, dados_completos, symbol, sinal, dca=False):
        try:
            direcao = sinal["direcao"]
            side = "buy" if direcao == "ALTA" else "sell"
            preco_atual = float(dados_completos["crus"][-1][4])
            alavancagem = sinal.get("alavancagem", 3)
            stop_loss = sinal.get("stop_loss")
            take_profit = sinal.get("take_profit")

            quantidade = self._calcular_quantidade(preco_atual, alavancagem, dca)

            ordem = {
                "symbol": symbol,
                "type": "market",
                "side": side,
                "amount": quantidade,
                "leverage": alavancagem,
            }

            params = {"leverage": alavancagem}
            if stop_loss:
                params["stopLossPrice"] = stop_loss
            if take_profit:
                params["takeProfitPrice"] = take_profit

            logger.info(f"Enviando ordem: {ordem}, params={params}")
            resposta = self._exchange.create_order(
                symbol=symbol,
                type="market",
                side=side,
                amount=quantidade,
                params=params,
            )

            ordem_id = resposta.get("id")
            if not dca:
                self._ordens_ativas[symbol] = ordem_id  # marca como ordem ativa

            return {
                "status": "EXECUTADO",
                "ordem_id": ordem_id,
                "resultado": resposta,
            }

        except Exception as e:
            logger.error(f"Erro ao executar ordem: {e}", exc_info=True)
            return {
                "status": "ERRO",
                "ordem_id": None,
                "resultado": str(e),
            }

    def _calcular_quantidade(self, preco, alavancagem, dca=False):
        try:
            saldo = self._exchange.fetch_balance()["free"]["USDT"]
            risco = self._config["trading"].get("risco_por_operacao", 0.01)
            percentual_dca = self._config["trading"].get("dca_percentual", 0.5)

            base = saldo * risco * alavancagem
            if dca:
                base *= percentual_dca

            quantidade = round(base / preco, 3)
            return max(quantidade, 0.01)
        except Exception as e:
            logger.error(f"Erro ao calcular quantidade: {e}", exc_info=True)
            return 0.01

    def finalizar(self):
        try:
            self._ordens_ativas.clear()
            logger.info("ExecucaoOrdens finalizado e ordens limpas")
        except Exception as e:
            logger.error(f"Erro ao finalizar plugin ExecucaoOrdens: {e}", exc_info=True)
