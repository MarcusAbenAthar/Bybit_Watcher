# execucao_ordens.py
from utils.logging_config import get_logger
import ccxt
from plugins.plugin import Plugin
from utils.config import carregar_config

logger = get_logger(__name__)


class ExecucaoOrdens(Plugin):
    PLUGIN_NAME = "execucao_ordens"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self._exchange = None
        self._ordens_pendentes = {}
        self._config = carregar_config()  # Carrega config padrão na inicialização

    def inicializar(self, config_dict: dict = None) -> bool:
        try:
            # Usa config passado ou mantém o padrão carregado
            self._config = config_dict or self._config
            if not super().inicializar(self._config):
                return False
            conexao = self._gerente.obter_plugin("plugins.conexao")
            if not conexao or not conexao.exchange:
                logger.error("Plugin de conexão não encontrado ou não inicializado")
                return False
            self._exchange = conexao.exchange
            self._exchange.set_sandbox_mode(True)  # Modo teste da Bybit
            auto_trade = self._config["trading"]["auto_trade"]
            logger.info(
                f"ExecucaoOrdens inicializado em modo teste (Auto Trade: {'ON' if auto_trade else 'OFF'})"
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar execucao_ordens: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "execucao_ordens": {"status": "NEUTRO", "ordem_id": None, "resultado": None}
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            if not isinstance(dados_completos, dict):
                logger.warning(
                    f"Dados devem ser um dicionário para {symbol} - {timeframe}"
                )
                return True

            sinal = self._extrair_sinal(dados_completos)
            if not sinal or sinal.get("direcao") == "NEUTRO":
                resultado = {
                    "status": "NEUTRO",
                    "ordem_id": None,
                    "resultado": "Nenhum sinal válido detectado",
                }
            else:
                self._exibir_sinal(sinal, symbol, timeframe)
                if self._config["trading"]["auto_trade"]:
                    resultado = self._executar_ordem_automatica(
                        dados_completos, symbol, timeframe
                    )
                else:
                    resultado = {
                        "status": "PRONTO",
                        "ordem_id": None,
                        "resultado": f"Sinal detectado: {sinal['direcao']} (Auto Trade OFF)",
                    }

            if isinstance(dados_completos, dict):
                dados_completos["execucao_ordens"] = resultado
            return True
        except Exception as e:
            logger.error(f"Erro ao executar execucao_ordens: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _extrair_sinal(self, dados_completos):
        try:
            for plugin in [
                "analise_candles",
                "medias_moveis",
                "price_action",
                "calculo_risco",
            ]:
                if (
                    plugin in dados_completos
                    and "direcao" in dados_completos[plugin]
                    and dados_completos[plugin]["direcao"] != "NEUTRO"
                ):
                    return dados_completos[plugin]
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair sinal: {e}")
            return None

    def _exibir_sinal(self, sinal, symbol, timeframe):
        try:
            mensagem = (
                f"Sinal detectado:\n"
                f"Par: {symbol}\n"
                f"Timeframe: {timeframe}\n"
                f"Direção: {sinal['direcao']}\n"
                f"Força: {sinal['forca']}\n"
                f"Confiança: {sinal['confianca']:.2f}\n"
                f"Stop Loss: {sinal.get('stop_loss', 'N/A')}\n"
                f"Take Profit: {sinal.get('take_profit', 'N/A')}"
            )
            logger.info(mensagem)
        except Exception as e:
            logger.error(f"Erro ao exibir sinal: {e}")

    def _executar_ordem_automatica(self, dados_completos, symbol, timeframe):
        try:
            sinal = self._extrair_sinal(dados_completos)
            if not sinal:
                return {
                    "status": "NEUTRO",
                    "ordem_id": None,
                    "resultado": "Nenhum sinal válido",
                }

            direcao = sinal["direcao"]
            stop_loss = sinal.get("stop_loss")
            take_profit = sinal.get("take_profit")
            alavancagem = dados_completos.get("calculo_alavancagem", 3)

            preco_atual = float(
                dados_completos["crus"][-1][4]
            )  # Último preço de fechamento
            quantidade = self._calcular_quantidade(preco_atual, alavancagem)

            ordem = {
                "symbol": symbol,
                "type": "market",
                "side": "buy" if direcao == "ALTA" else "sell",
                "amount": quantidade,
                "leverage": alavancagem,
            }

            if stop_loss:
                ordem["stopLossPrice"] = stop_loss
            if take_profit:
                ordem["takeProfitPrice"] = take_profit

            logger.info(f"Executando ordem automática: {ordem}")
            resposta = self._exchange.create_order(
                symbol=symbol,
                type="market",
                side=ordem["side"],
                amount=quantidade,
                params={
                    "leverage": alavancagem,
                    "stopLossPrice": stop_loss,
                    "takeProfitPrice": take_profit,
                },
            )

            ordem_id = resposta.get("id")
            self._ordens_pendentes[ordem_id] = ordem
            return {"status": "EXECUTADO", "ordem_id": ordem_id, "resultado": resposta}
        except Exception as e:
            logger.error(f"Erro ao executar ordem automática: {e}")
            return {"status": "ERRO", "ordem_id": None, "resultado": str(e)}

    def _calcular_quantidade(self, preco_atual, alavancagem):
        try:
            saldo = self._exchange.fetch_balance()["free"]["USDT"]
            risco = self._config["trading"]["risco_por_operacao"]  # Ex.: 0.01 (1%)
            quantidade_base = (saldo * risco * alavancagem) / preco_atual
            return round(quantidade_base, 3)  # Ajuste de precisão
        except Exception as e:
            logger.error(f"Erro ao calcular quantidade: {e}")
            return 0.01  # Quantidade mínima padrão
