"""
Plugin de execução de ordens.
Responsabilidade única: executar ordens de acordo com sinais e regras.
Não deve registrar, inicializar ou finalizar automaticamente.
Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
"""

from utils.logging_config import get_logger, log_rastreamento
from utils.config import carregar_config
from plugins.plugin import Plugin
import ccxt
from datetime import datetime
from utils.plugin_utils import validar_klines

logger = get_logger(__name__)


class ExecucaoOrdens(Plugin):
    """
    Plugin para executar ordens de compra/venda com SL/TP, incluindo reentradas (DCA) e controle de posição ativa.
    - Responsabilidade única: execução de ordens e gerenciamento de posições.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "execucao_ordens"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["execucao", "ordens", "trading"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin ExecucaoOrdens.
        """
        return ["conexao", "sinais_plugin", "gerenciador_banco"]

    def __init__(self, gerente=None, **kwargs):
        """
        Inicializa o plugin ExecucaoOrdens.

        Args:
            gerente: Instância do plugin Gerente.
            **kwargs: Outras dependências.
        """
        super().__init__(**kwargs)
        self._gerente = gerente
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("execucao_ordens", {}).copy()
            if "plugins" in config and "execucao_ordens" in config["plugins"]
            else {}
        )
        self._exchange = None
        self._ordens_ativas = {}

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

            # Corrigir acesso à dependência de conexão
            conexao_plugin = (
                self._gerente.obter_plugin("conexao") if self._gerente else None
            )
            if not conexao_plugin or not hasattr(conexao_plugin, "exchange"):
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

            self._exchange = conexao_plugin.exchange
            self._exchange.set_sandbox_mode(True)
            logger.info(f"[{self.nome}] Inicializado em modo sandbox")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> dict:
        """
        Executa ordens com base nos sinais fornecidos.
        Aceita tanto dados_completos['sinais'] quanto campos diretos (direcao, preco_atual, etc).
        Sempre retorna um dicionário de resultado, mesmo em caso de erro.
        """
        symbol = kwargs.get("symbol")
        market_id = kwargs.get("market_id")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"execucao_ordens/{symbol or market_id}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        symbol_or_id = market_id or symbol

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
            return {"erro": "dados_completos não é um dicionário"}

        if not all([symbol_or_id, timeframe]):
            logger.error(
                f"[{self.nome}] Parâmetros obrigatórios ausentes (symbol_or_id={symbol_or_id}, timeframe={timeframe})"
            )
            return {"erro": "Parâmetros obrigatórios ausentes"}

        # Aceita tanto 'sinais' quanto campos diretos
        tem_sinais = isinstance(dados_completos.get("sinais"), dict)
        tem_direto = all(
            k in dados_completos
            for k in [
                "direcao",
                "preco_atual",
                "alavancagem",
                "stop_loss",
                "take_profit",
            ]
        )
        if not (tem_sinais or (tem_direto and dados_completos.get("crus"))):
            logger.error(f"[{self.nome}] Sinais ou crus ausentes em dados_completos")
            return {"erro": "Sinais ou crus ausentes em dados_completos"}

        sinal = self._extrair_sinal(dados_completos)
        # Se não houver 'sinais', monta sinal a partir dos campos diretos
        if not sinal and tem_direto:
            sinal = {
                "direcao": dados_completos["direcao"],
                "preco_atual": dados_completos["preco_atual"],
                "alavancagem": dados_completos["alavancagem"],
                "stop_loss": dados_completos["stop_loss"],
                "take_profit": dados_completos["take_profit"],
            }
        direcao = sinal.get("direcao")
        if direcao not in ["LONG", "SHORT", "ALTA", "BAIXA"]:
            logger.info(
                f"[{self.nome}] Nenhum sinal válido para {symbol_or_id} ({direcao})"
            )
            return {"erro": f"Nenhum sinal válido para {symbol_or_id} ({direcao})"}

        auto_trade = self._config.get("trading", {}).get("auto_trade", False)
        if not auto_trade:
            logger.info(f"[{self.nome}] Auto Trade desativado para {symbol_or_id}")
            return {"info": "Auto Trade desativado"}

        try:
            if symbol_or_id in self._ordens_ativas and self._verificar_ordem_ativa(
                symbol_or_id
            ):
                logger.info(f"[{self.nome}] Reentrada DCA para {symbol_or_id}")
                resultado = self._executar_ordem(
                    dados_completos, symbol_or_id, sinal, dca=True
                )
            else:
                logger.info(f"[{self.nome}] Ordem principal para {symbol_or_id}")
                resultado = self._executar_ordem(dados_completos, symbol_or_id, sinal)
            return resultado
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return {"erro": str(e)}

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

    def _verificar_ordem_ativa(self, symbol_or_id: str) -> bool:
        """
        Verifica se a ordem ativa ainda está aberta.

        Args:
            symbol_or_id: ID do mercado ou symbol.

        Returns:
            bool: True se ordem ativa, False caso contrário.
        """
        try:
            ordem_id = self._ordens_ativas.get(symbol_or_id)
            if not ordem_id:
                return False
            ordem = self._exchange.fetch_order(ordem_id, symbol_or_id)
            if ordem["status"] in ["open", "pending"]:
                return True
            del self._ordens_ativas[symbol_or_id]
            return False
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao verificar ordem ativa para {symbol_or_id}: {e}"
            )
            del self._ordens_ativas[symbol_or_id]
            return False

    def _executar_ordem(
        self, dados_completos: dict, symbol_or_id: str, sinal: dict, dca: bool = False
    ) -> dict:
        """
        Executa uma ordem de mercado.

        Args:
            dados_completos: Dicionário com dados de análise.
            symbol_or_id: ID do mercado ou symbol.
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
            side = "buy" if direcao == "LONG" else "sell"
            alavancagem = sinal.get("alavancagem", 3.0)
            sl = sinal.get("stop_loss")
            tp = sinal.get("take_profit")
            # Corrigir: nunca permitir None em SL/TP
            if sl is None:
                sl = 0.0
            if tp is None:
                tp = 0.0

            crus = dados_completos.get("crus", [])
            if not crus or not isinstance(crus[-1], (list, tuple)) or len(crus[-1]) < 5:
                logger.error(f"[{self.nome}] crus inválido para {symbol_or_id}")
                return {
                    "status": "ERRO",
                    "ordem_id": None,
                    "resultado": "Dados crus inválidos",
                }
            preco_atual = float(crus[-1][4])

            # Validar limites da exchange
            # Busca o market pelo id ou symbol (prioriza id)
            market = self._exchange.markets.get(symbol_or_id, {})
            min_amount = market.get("limits", {}).get("amount", {}).get("min", 0.01)
            precision = market.get("precision", {}).get("amount", 3)

            quantidade = self._calcular_quantidade(preco_atual, alavancagem, dca)
            if quantidade < min_amount:
                logger.error(
                    f"[{self.nome}] Quantidade {quantidade} abaixo do mínimo {min_amount} para {symbol_or_id}"
                )
                return {
                    "status": "ERRO",
                    "ordem_id": None,
                    "resultado": f"Quantidade abaixo do mínimo ({min_amount})",
                }
            quantidade = round(quantidade, precision)

            ordem = {
                "symbol": symbol_or_id,
                "type": "market",
                "side": side,
                "amount": quantidade,
                "leverage": alavancagem,
            }

            params = {"leverage": alavancagem}
            if sl is not None:
                params["stopLossPrice"] = sl
            if tp is not None:
                params["takeProfitPrice"] = tp

            logger.info(
                f"[{self.nome}] Enviando ordem para {symbol_or_id}: {ordem}, params={params}"
            )
            resposta = self._exchange.create_order(
                symbol=symbol_or_id,
                type="market",
                side=side,
                amount=quantidade,
                params=params,
            )

            ordem_id = resposta.get("id")
            if not dca:
                self._ordens_ativas[symbol_or_id] = ordem_id

            # Exemplo de uso:
            self.log_banco(
                tabela="ordens_executadas",
                operacao="INSERT",
                dados={
                    "order_id": ordem_id,
                    "symbol": ordem["symbol"],
                    "timestamp": datetime.now(),
                    "tipo": ordem["type"],
                    "lado": ordem["side"],
                    "preco": ordem.get("price"),
                    "quantidade": ordem["amount"],
                    "status": "OPEN",
                    "sinal_origem": sinal.get("id", "desconhecido"),
                },
            )

            return {
                "status": "EXECUTADO",
                "ordem_id": ordem_id,
                "resultado": resposta,
            }
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao executar ordem para {symbol_or_id}: {e}",
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
            for symbol_or_id, ordem_id in list(self._ordens_ativas.items()):
                try:
                    ordem = self._exchange.fetch_order(ordem_id, symbol_or_id)
                    if ordem["status"] in ["open", "pending"]:
                        self._exchange.cancel_order(ordem_id, symbol_or_id)
                        logger.info(
                            f"[{self.nome}] Ordem {ordem_id} cancelada para {symbol_or_id}"
                        )
                except Exception as e:
                    logger.error(
                        f"[{self.nome}] Erro ao cancelar ordem {ordem_id} para {symbol_or_id}: {e}"
                    )
            self._ordens_ativas.clear()
            logger.info(f"[{self.nome}] Finalizado e ordens limpas")
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao finalizar: {e}", exc_info=True)

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "ordens_executadas": {
                "descricao": "Armazena ordens executadas, incluindo score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "order_id": "VARCHAR(50) PRIMARY KEY",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "tipo": "VARCHAR(10)",
                    "lado": "VARCHAR(5)",
                    "preco": "DECIMAL(18,8)",
                    "quantidade": "DECIMAL(18,8)",
                    "status": "VARCHAR(15)",
                    "sinal_origem": "VARCHAR(50)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
            "historico_ordens": {
                "descricao": "Armazena histórico de eventos das ordens, incluindo score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "order_id": "VARCHAR(50) REFERENCES ordens_executadas(order_id)",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "evento": "VARCHAR(20)",
                    "preco_executado": "DECIMAL(18,8)",
                    "quantidade_executada": "DECIMAL(18,8)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
