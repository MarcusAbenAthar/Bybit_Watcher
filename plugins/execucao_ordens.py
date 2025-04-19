"""
Plugin para executar ordens de compra/venda com SL/TP, incluindo reentradas (DCA) e controle de posição ativa.
"""

from utils.logging_config import get_logger
from utils.config import carregar_config
from plugins.plugin import Plugin
import ccxt

logger = get_logger(__name__)


class ExecucaoOrdens(Plugin):
    PLUGIN_NAME = "execucao_ordens"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["execucao", "ordens", "trading"]
    PLUGIN_PRIORIDADE = 100

    def __init__(self, conexao=None, **kwargs):
        """
        Inicializa o plugin ExecucaoOrdens.

        Args:
            conexao: Instância do plugin Conexao.
            **kwargs: Outras dependências.
        """
        super().__init__(**kwargs)
        self._conexao = conexao
        self._exchange = None
        self._ordens_ativas = {}
        self._config = None  # Inicializado em inicializar

    def inicializar(self, config_dict: dict = None) -> bool:
        """
        Inicializa o plugin com configurações fornecidas.

        Args:
            config_dict: Dicionário com configurações.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            self._config = config_dict or carregar_config()
            if not super().inicializar(self._config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            if not self._conexao or not self._conexao.exchange:
                logger.error(
                    f"[{self.nome}] Plugin de conexão não encontrado ou não inicializado"
                )
                return False

            trading_config = self._config.get("trading", {})
            required_keys = ["risco_por_operacao", "dca_percentual", "auto_trade"]
            if not all(k in trading_config for k in required_keys):
                logger.error(
                    f"[{self.nome}] Configurações de trading incompletas: {trading_config}"
                )
                return False
            if not (
                isinstance(trading_config["risco_por_operacao"], (int, float))
                and 0.0 < trading_config["risco_por_operacao"] <= 1.0
            ):
                logger.error(
                    f"[{self.nome}] risco_por_operacao inválido: {trading_config['risco_por_operacao']}"
                )
                return False
            if not (
                isinstance(trading_config["dca_percentual"], (int, float))
                and 0.0 < trading_config["dca_percentual"] <= 1.0
            ):
                logger.error(
                    f"[{self.nome}] dca_percentual inválido: {trading_config['dca_percentual']}"
                )
                return False

            self._exchange = self._conexao.exchange
            self._exchange.set_sandbox_mode(True)
            logger.info(f"[{self.nome}] Inicializado em modo sandbox")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa ordens com base nos sinais fornecidos.

        Args:
            dados_completos (dict): Dados de análise com sinais.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")

        resultado_padrao = {
            "execucao_ordens": {
                "status": "LATERAL",
                "ordem_id": None,
                "resultado": None,
            }
        }

        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            dados_completos["execucao_ordens"] = resultado_padrao["execucao_ordens"]
            return True

        if not all([symbol, timeframe]):
            logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
            dados_completos["execucao_ordens"] = resultado_padrao["execucao_ordens"]
            return True

        if not dados_completos.get("sinais") or not dados_completos.get("crus"):
            logger.error(f"[{self.nome}] Sinais ou crus ausentes em dados_completos")
            dados_completos["execucao_ordens"] = resultado_padrao["execucao_ordens"]
            return True

        sinal = self._extrair_sinal(dados_completos)
        if not sinal or sinal.get("direcao") in ["LATERAL", "NEUTRO"]:
            logger.info(
                f"[{self.nome}] Nenhum sinal válido para {symbol} ({sinal.get('direcao', 'N/A')})"
            )
            dados_completos["execucao_ordens"] = resultado_padrao["execucao_ordens"]
            return True

        auto_trade = self._config.get("trading", {}).get("auto_trade", False)
        if not auto_trade:
            logger.info(f"[{self.nome}] Auto Trade desativado para {symbol}")
            dados_completos["execucao_ordens"] = {
                "status": "PRONTO",
                "ordem_id": None,
                "resultado": "Sinal válido detectado - aguardando confirmação manual",
            }
            return True

        try:
            if symbol in self._ordens_ativas and self._verificar_ordem_ativa(symbol):
                logger.info(f"[{self.nome}] Reentrada DCA para {symbol}")
                resultado = self._executar_ordem(
                    dados_completos, symbol, sinal, dca=True
                )
            else:
                logger.info(f"[{self.nome}] Ordem principal para {symbol}")
                resultado = self._executar_ordem(dados_completos, symbol, sinal)
            dados_completos["execucao_ordens"] = resultado
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            dados_completos["execucao_ordens"] = {
                "status": "ERRO",
                "ordem_id": None,
                "resultado": str(e),
            }
            return True

    def _extrair_sinal(self, dados_completos: dict) -> dict:
        """
        Extrai o sinal de dados_completos.

        Args:
            dados_completos: Dicionário com dados de análise.

        Returns:
            dict: Sinal extraído ou vazio.
        """
        try:
            return dados_completos.get("sinais", {})
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair sinal: {e}")
            return {}

    def _verificar_ordem_ativa(self, symbol: str) -> bool:
        """
        Verifica se a ordem ativa ainda está aberta.

        Args:
            symbol: Símbolo do par.

        Returns:
            bool: True se ordem ativa, False caso contrário.
        """
        try:
            ordem_id = self._ordens_ativas.get(symbol)
            if not ordem_id:
                return False
            ordem = self._exchange.fetch_order(ordem_id, symbol)
            if ordem["status"] in ["open", "pending"]:
                return True
            del self._ordens_ativas[symbol]
            return False
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao verificar ordem ativa para {symbol}: {e}"
            )
            del self._ordens_ativas[symbol]
            return False

    def _executar_ordem(
        self, dados_completos: dict, symbol: str, sinal: dict, dca: bool = False
    ) -> dict:
        """
        Executa uma ordem de mercado.

        Args:
            dados_completos: Dicionário com dados de análise.
            symbol: Símbolo do par.
            sinal: Dicionário com sinal.
            dca: Se True, aplica percentual DCA.

        Returns:
            dict: Resultado da ordem.
        """
        try:
            if sinal.get("direcao") not in ["ALTA", "BAIXA"]:
                logger.error(f"[{self.nome}] Direção inválida: {sinal.get('direcao')}")
                return {
                    "status": "ERRO",
                    "ordem_id": None,
                    "resultado": "Direção inválida",
                }

            direcao = sinal["direcao"]
            side = "buy" if direcao == "ALTA" else "sell"
            alavancagem = sinal.get("alavancagem", 3.0)
            stop_loss = sinal.get("stop_loss")
            take_profit = sinal.get("take_profit")

            crus = dados_completos.get("crus", [])
            if not crus or not isinstance(crus[-1], (list, tuple)) or len(crus[-1]) < 5:
                logger.error(f"[{self.nome}] crus inválido para {symbol}")
                return {
                    "status": "ERRO",
                    "ordem_id": None,
                    "resultado": "Dados crus inválidos",
                }
            preco_atual = float(crus[-1][4])

            # Validar limites da exchange
            market = self._exchange.markets.get(symbol, {})
            min_amount = market.get("limits", {}).get("amount", {}).get("min", 0.01)
            precision = market.get("precision", {}).get("amount", 3)

            quantidade = self._calcular_quantidade(preco_atual, alavancagem, dca)
            if quantidade < min_amount:
                logger.error(
                    f"[{self.nome}] Quantidade {quantidade} abaixo do mínimo {min_amount} para {symbol}"
                )
                return {
                    "status": "ERRO",
                    "ordem_id": None,
                    "resultado": f"Quantidade abaixo do mínimo ({min_amount})",
                }
            quantidade = round(quantidade, precision)

            ordem = {
                "symbol": symbol,
                "type": "market",
                "side": side,
                "amount": quantidade,
                "leverage": alavancagem,
            }

            params = {"leverage": alavancagem}
            if stop_loss is not None:
                params["stopLossPrice"] = stop_loss
            if take_profit is not None:
                params["takeProfitPrice"] = take_profit

            logger.info(
                f"[{self.nome}] Enviando ordem para {symbol}: {ordem}, params={params}"
            )
            resposta = self._exchange.create_order(
                symbol=symbol,
                type="market",
                side=side,
                amount=quantidade,
                params=params,
            )

            ordem_id = resposta.get("id")
            if not dca:
                self._ordens_ativas[symbol] = ordem_id

            return {
                "status": "EXECUTADO",
                "ordem_id": ordem_id,
                "resultado": resposta,
            }
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao executar ordem para {symbol}: {e}",
                exc_info=True,
            )
            return {
                "status": "ERRO",
                "ordem_id": None,
                "resultado": str(e),
            }

    def _calcular_quantidade(
        self, preco: float, alavancagem: float, dca: bool = False
    ) -> float:
        """
        Calcula a quantidade com base no risco e alavancagem.

        Args:
            preco: Preço atual do ativo.
            alavancagem: Valor da alavancagem.
            dca: Se True, aplica percentual DCA.

        Returns:
            float: Quantidade calculada.
        """
        try:
            saldo = self._exchange.fetch_balance().get("free", {}).get("USDT", 0.0)
            if saldo <= 0:
                logger.error(f"[{self.nome}] Saldo insuficiente: {saldo} USDT")
                return 0.01

            risco = self._config["trading"].get("risco_por_operacao", 0.01)
            percentual_dca = self._config["trading"].get("dca_percentual", 0.5)

            base = saldo * risco * alavancagem
            if dca:
                base *= percentual_dca

            quantidade = round(base / preco, 3)
            return max(quantidade, 0.01)
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao calcular quantidade: {e}", exc_info=True
            )
            return 0.01

    def finalizar(self):
        """
        Finaliza o plugin, cancelando ordens ativas e limpando estado.
        """
        try:
            for symbol, ordem_id in list(self._ordens_ativas.items()):
                try:
                    ordem = self._exchange.fetch_order(ordem_id, symbol)
                    if ordem["status"] in ["open", "pending"]:
                        self._exchange.cancel_order(ordem_id, symbol)
                        logger.info(
                            f"[{self.nome}] Ordem {ordem_id} cancelada para {symbol}"
                        )
                except Exception as e:
                    logger.error(
                        f"[{self.nome}] Erro ao cancelar ordem {ordem_id} para {symbol}: {e}"
                    )
            self._ordens_ativas.clear()
            logger.info(f"[{self.nome}] Finalizado e ordens limpas")
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao finalizar: {e}", exc_info=True)
