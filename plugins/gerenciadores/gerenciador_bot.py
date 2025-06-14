"""Gerenciador principal do bot de trading - versão inteligente com paralelismo."""

from utils.logging_config import get_logger, log_rastreamento, log_dados
from plugins.gerenciadores.gerenciador import BaseGerenciador
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from time import time
from typing import List
from utils.config import carregar_config
from utils.plugin_utils import validar_klines

logger = get_logger(__name__)


class GerenciadorBot(BaseGerenciador):
    """Gerenciador central e inteligente do bot."""

    PLUGIN_NAME = "gerenciador_bot"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["core", "controle"]

    def __init__(self, gerente=None, **kwargs):
        super().__init__(**kwargs)
        self._gerente = gerente  # Essencial para acessar plugins
        self._status = "parado"
        # Lê o número de workers do config centralizado
        config = carregar_config()
        max_workers = (
            config.get("gerenciadores", {})
            .get("bot", {})
            .get("executor_max_workers", 4)
        )
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers
        )  # Paralelismo ajustável via config
        self._estado_ativo = defaultdict(dict)  # Guarda o status por par e timeframe

    def configuracoes_requeridas(self) -> List[str]:
        """
        Retorna lista de chaves obrigatórias no config.

        Returns:
            List[str]: Chaves necessárias no dicionário de configuração.
        """
        return ["pares", "timeframes"]

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o GerenciadorBot com validação de configurações.

        Args:
            config: Configurações com chaves 'pares' e 'timeframes' não vazias.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                return False

            if not config["pares"] or not config["timeframes"]:
                logger.error("Configuração inválida: pares ou timeframes vazios")
                return False

            self._status = "iniciando"
            logger.info("GerenciadorBot inicializado")
            return True
        except KeyError as e:
            logger.error(f"Chave de configuração ausente: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao inicializar GerenciadorBot: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o ciclo principal do bot, processando pares e timeframes em paralelo.

        Returns:
            bool: True se todos os processamentos foram bem-sucedidos, False caso contrário.
        """
        if self._status != "rodando":
            logger.warning("Bot não está rodando")
            return False

        try:
            # Loga dados no início do ciclo
            log_dados(
                componente="gerenciador_bot",
                acao="inicio_ciclo",
                dados={"args": args, "kwargs": kwargs},
            )
            pares = self._config["pares"]
            timeframes = self._config["timeframes"]

            # Filtrar pares inválidos usando Conexao.listar_pares()
            conexao = self._gerente.obter_plugin("conexao")
            if conexao and hasattr(conexao, "listar_pares"):
                pares_validos = conexao.listar_pares()
                invalidos = [p for p in pares if p not in pares_validos and p != "all"]
                if invalidos:
                    logger.warning(f"Pares inválidos removidos: {invalidos}")
                pares = [p for p in pares if p in pares_validos or p == "all"]
            else:
                logger.warning(
                    "Não foi possível filtrar pares: plugin Conexao ausente ou sem listar_pares()"
                )

            # NOVO: se 'pares' for ['all'], busca todos os símbolos disponíveis na exchange
            if pares == ["all"]:
                conexao_plugin = self._gerente.obter_plugin("conexao")
                if (
                    not conexao_plugin
                    or not hasattr(conexao_plugin, "exchange")
                    or not conexao_plugin.exchange
                ):
                    logger.error(
                        "Plugin de conexão não disponível ou não inicializado para buscar todos os pares."
                    )
                    return False
                try:
                    markets = conexao_plugin.exchange.load_markets()
                    spot = self._config.get("spot", False)
                    futuros = self._config.get("futuros", True)
                    # Novo filtro robusto para pares USDT
                    # Determina dinamicamente os tipos de mercado a filtrar a partir do config
                    tipos_mercado = [
                        k
                        for k in ["spot", "futuros", "swap", "option"]
                        if self._config.get(k, False)
                    ]
                    # Mapeia 'futuros' -> 'future' para o campo type
                    tipos_ccxt = [
                        t if t != "futuros" else "future" for t in tipos_mercado
                    ]

                    pares_filtrados = []
                    symbol_to_id = {}
                    for symbol, info in markets.items():
                        tipo = info.get("type")
                        quote_coin = info.get("quoteCoin") or info.get("quote")
                        settle_coin = info.get("settleCoin") or info.get("settle")
                        market_id = info.get("id", symbol)
                        if tipo in tipos_ccxt:
                            if tipo == "spot" and quote_coin == "USDT":
                                pares_filtrados.append(market_id)
                                symbol_to_id[symbol] = market_id
                            elif (
                                tipo in ["future", "swap", "option"]
                                and quote_coin == "USDT"
                                and settle_coin == "USDT"
                            ):
                                pares_filtrados.append(market_id)
                                symbol_to_id[symbol] = market_id
                    if not pares_filtrados:
                        logger.error(
                            f"Nenhum par USDT encontrado com os filtros: spot={self._config.get('spot', False)}, futuros={self._config.get('futuros', False)}, swap={self._config.get('swap', False)}, option={self._config.get('option', False)}."
                        )
                        return False
                    # Loga apenas os IDs dos mercados
                    logger.info(
                        f"Busca dinâmica de pares: {len(markets)} pares totais, {len(pares_filtrados)} IDs USDT utilizados: {[s for s in pares_filtrados]}"
                    )
                    pares = pares_filtrados
                    self._symbol_to_id = (
                        symbol_to_id  # mapping symbol->id para uso futuro
                    )
                except Exception as e:
                    logger.error(f"Erro ao buscar todos os pares da exchange: {e}")
                    return False
            else:
                logger.info(f"Usando pares definidos na configuração: {pares}")
            plugins_analise = [
                p
                for p in self._gerente.filtrar_por_tag("analise")
                if p.nome != "analisador_mercado"
            ]
            analisador_mercado = self._gerente.obter_plugin("analisador_mercado")
            sinais_plugin = self._gerente.obter_plugin("sinais_plugin")

            if not sinais_plugin:
                logger.error("Plugin sinais_plugin não encontrado")
                return False
            if not analisador_mercado:
                logger.error("Plugin analisador_mercado não encontrado")
                return False

            logger.execution(f"Iniciando ciclo para {len(pares)} pares")

            # Processamento em lote (batch) de symbols
            from itertools import islice

            batch_size = self._config.get("batch_size", 3)

            def batcher(iterable, n):
                it = iter(iterable)
                while True:
                    batch = list(islice(it, n))
                    if not batch:
                        break
                    yield batch

            resultados_gerais = []
            # Buffer para armazenar sinais por símbolo/timeframe
            buffer_sinais = {symbol: {} for symbol in pares}

            # Obter o consolidador de sinais
            consolidador = self._gerente.obter_plugin("consolidador_sinais")
            if not consolidador:
                logger.error("Plugin consolidador_sinais não encontrado")
                return False

            for symbol_batch in batcher(pares, batch_size):
                tarefas = [
                    self._executor.submit(
                        self._processar_par,
                        symbol,
                        tf,
                        plugins_analise,
                        sinais_plugin,
                        buffer_sinais,
                    )
                    for symbol in symbol_batch
                    for tf in timeframes
                ]
                resultados = [t.result() for t in as_completed(tarefas)]
                resultados_gerais.extend(resultados)
                logger.execution(f"Batch finalizado para symbols: {symbol_batch}")

                # Após cada batch, consolidar sinais dos símbolos processados
                for symbol in symbol_batch:
                    if all(tf in buffer_sinais[symbol] for tf in timeframes):
                        for tf in timeframes:
                            # Loga dados antes do processamento de cada timeframe
                            log_dados(
                                componente="gerenciador_bot",
                                acao=f"antes_analise_{symbol}_{tf}",
                                dados=buffer_sinais[symbol][tf],
                            )
                            logger.debug(
                                f"[pipeline] Antes do consolidador: {symbol}-{tf} chaves = {list(buffer_sinais[symbol][tf].keys())}"
                            )
                        # Monta dicionário de dados completos para todos os timeframes
                        dados_timeframes = {}
                        for tf in timeframes:
                            dados_tf = buffer_sinais[symbol].get(tf, {})
                            # Garante que todos os campos essenciais estejam presentes
                            dados_timeframes[tf] = dados_tf.copy()

                        # Adiciona o symbol ao dicionário de timeframes
                        dados_completos = {
                            "symbol": symbol,
                            "timeframes": dados_timeframes,
                        }

                        logger.debug(
                            f"[pipeline] Dados enviados ao consolidador para {symbol}: chaves = {list(dados_timeframes.keys())}"
                        )

                        # Antes do consolidador
                        log_dados(
                            componente="gerenciador_bot",
                            acao=f"antes_consolidador_{symbol}",
                            dados=dados_completos,
                        )
                        sinal_final = consolidador.executar(
                            dados_completos=dados_completos
                        )
                        log_dados(
                            componente="gerenciador_bot",
                            acao=f"apos_consolidador_{symbol}",
                            dados=sinal_final,
                        )
                        # Propaga o resultado para o buffer
                        buffer_sinais[symbol]["sinal_final"] = sinal_final

            logger.execution(f"Ciclo finalizado para todos os pares")
            # Loga dados ao final do ciclo
            log_dados(
                componente="gerenciador_bot", acao="fim_ciclo", dados=buffer_sinais
            )
            return all(resultados_gerais)
        except Exception as e:
            logger.error(f"Erro geral no ciclo do bot: {e}", exc_info=True)
            return False

    def _processar_par(
        self, symbol, timeframe, plugins_analise, sinais_plugin, buffer_sinais=None
    ) -> bool:
        """
        Processa um par/timeframe, executando plugins de análise e sinais.
        """
        try:
            logger.execution(f"Início do processamento: {symbol} - {timeframe}")
            dados_completos = {}
            dados_completos["symbol"] = symbol
            dados_completos["timeframe"] = timeframe

            # Popula k-lines via plugin ObterDados antes das análises
            obter_dados = self._gerente.obter_plugin("obter_dados")
            if obter_dados:
                obter_dados.executar(
                    dados_completos=dados_completos, symbol=symbol, timeframe=timeframe
                )
                crus = dados_completos.get("crus", [])
                logger.debug(
                    f"[pipeline] Crus obtidos para {symbol}-{timeframe}: {len(crus) if crus else 0}"
                )
                dados_completos["crus"] = crus

            # Executa plugins de análise
            for plugin in plugins_analise:
                if hasattr(plugin, "executar"):
                    resultado = plugin.executar(
                        dados_completos=dados_completos,
                        symbol=symbol,
                        timeframe=timeframe,
                    )
                    if isinstance(resultado, dict):
                        dados_completos.update(resultado)
                    logger.debug(
                        f"[pipeline] Após {plugin.nome}: chaves em dados_completos = {list(dados_completos.keys())}"
                    )

            # Garante que symbol, timeframe e crus estejam presentes
            if not all(
                [
                    dados_completos.get("symbol"),
                    dados_completos.get("timeframe"),
                    dados_completos.get("crus"),
                ]
            ):
                logger.error(
                    f"[pipeline] Dados incompletos para {symbol}-{timeframe} antes do consolidador: {dados_completos}"
                )
                return False

            # Executa o plugin de sinais (analise_mercado consolidada)
            if sinais_plugin and hasattr(sinais_plugin, "executar"):
                resultado_sinais = sinais_plugin.executar(
                    symbol=symbol,
                    timeframe=timeframe,
                    dados_completos=dados_completos,
                )
                log_dados(
                    componente="gerenciador_bot",
                    acao=f"apos_sinais_plugin_{symbol}_{timeframe}",
                    dados=resultado_sinais,
                )
                logger.debug(
                    f"[pipeline] Após sinais_plugin: {list(dados_completos.keys())}"
                )
                if isinstance(resultado_sinais, dict):
                    dados_completos.update(resultado_sinais)

            # Buffer de sinais, se necessário
            if buffer_sinais is not None:
                # Armazene o dicionário COMPLETO de dados_completos para cada timeframe
                from copy import deepcopy

                # Antes de armazenar no buffer
                log_dados(
                    componente="gerenciador_bot",
                    acao=f"antes_buffer_{symbol}_{timeframe}",
                    dados=dados_completos,
                )
                buffer_sinais[symbol][timeframe] = deepcopy(dados_completos)

            self._estado_ativo[symbol][timeframe] = {"timestamp": time()}
            logger.execution(f"Fim do processamento: {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.error(
                f"[pipeline] Erro no processamento de {symbol}-{timeframe}: {e}",
                exc_info=True,
            )
            return False

    def iniciar(self) -> bool:
        """
        Inicia a execução do bot.

        Returns:
            bool: True se iniciado com sucesso, False caso contrário.
        """
        try:
            self._status = "rodando"
            logger.info("Bot em execução")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}", exc_info=True)
            return False

    def parar(self) -> bool:
        """
        Para a execução do bot.

        Returns:
            bool: True se parado com sucesso, False caso contrário.
        """
        try:
            self._status = "parado"
            logger.info("Bot pausado")
            return True
        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}", exc_info=True)
            return False

    def finalizar(self) -> bool:
        """
        Finaliza o gerenciador, encerrando o ThreadPoolExecutor e limpando estado.

        Returns:
            bool: True se finalizado com sucesso, False caso contrário.
        """
        try:
            self.parar()
            self._executor.shutdown(wait=True)
            super().finalizar()
            logger.debug("GerenciadorBot finalizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao finalizar GerenciadorBot: {e}")
            return False

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "ciclos_bot": {
                "descricao": "Armazena logs dos ciclos do bot, incluindo status, contexto, observações e rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "status": "VARCHAR(20)",
                    "pares": "JSONB",
                    "timeframes": "JSONB",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "detalhes": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
