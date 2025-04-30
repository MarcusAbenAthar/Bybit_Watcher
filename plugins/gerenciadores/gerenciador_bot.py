"""Gerenciador principal do bot de trading - versão inteligente com paralelismo."""

from utils.logging_config import get_logger
from plugins.gerenciadores.gerenciador import BaseGerenciador
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from time import time
from typing import List

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
        self._executor = ThreadPoolExecutor(max_workers=4)  # Paralelismo ajustável
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
                logger.warning("Não foi possível filtrar pares: plugin Conexao ausente ou sem listar_pares()")

            # NOVO: se 'pares' for ['all'], busca todos os símbolos disponíveis na exchange
            if pares == ["all"]:
                conexao_plugin = self._gerente.obter_plugin("conexao")
                if not conexao_plugin or not hasattr(conexao_plugin, "exchange") or not conexao_plugin.exchange:
                    logger.error("Plugin de conexão não disponível ou não inicializado para buscar todos os pares.")
                    return False
                try:
                    markets = conexao_plugin.exchange.load_markets()
                    spot = self._config.get("spot", False)
                    futuros = self._config.get("futuros", True)
                    # Novo filtro robusto para pares USDT
                    # Determina dinamicamente os tipos de mercado a filtrar a partir do config
                    tipos_mercado = [k for k in ['spot', 'futuros', 'swap', 'option'] if self._config.get(k, False)]
                    # Mapeia 'futuros' -> 'future' para o campo type
                    tipos_ccxt = [t if t != 'futuros' else 'future' for t in tipos_mercado]

                    pares_filtrados = []
                    symbol_to_id = {}
                    for symbol, info in markets.items():
                        tipo = info.get('type')
                        quote_coin = info.get('quoteCoin') or info.get('quote')
                        settle_coin = info.get('settleCoin') or info.get('settle')
                        market_id = info.get('id', symbol)
                        if tipo in tipos_ccxt:
                            if tipo == 'spot' and quote_coin == 'USDT':
                                pares_filtrados.append(market_id)
                                symbol_to_id[symbol] = market_id
                            elif tipo in ['future', 'swap', 'option'] and quote_coin == 'USDT' and settle_coin == 'USDT':
                                pares_filtrados.append(market_id)
                                symbol_to_id[symbol] = market_id
                    if not pares_filtrados:
                        logger.error(f"Nenhum par USDT encontrado com os filtros: spot={self._config.get('spot', False)}, futuros={self._config.get('futuros', False)}, swap={self._config.get('swap', False)}, option={self._config.get('option', False)}.")
                        return False
                    # Loga apenas os IDs dos mercados
                    logger.info(f"Busca dinâmica de pares: {len(markets)} pares totais, {len(pares_filtrados)} IDs USDT utilizados: {[s for s in pares_filtrados]}")
                    pares = pares_filtrados
                    self._symbol_to_id = symbol_to_id  # mapping symbol->id para uso futuro
                except Exception as e:
                    logger.error(f"Erro ao buscar todos os pares da exchange: {e}")
                    return False
            else:
                logger.info(f"Usando pares definidos na configuração: {pares}")
            plugins_analise = [p for p in self._gerente.filtrar_por_tag("analise") if p.nome != "analisador_mercado"]
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
            for symbol_batch in batcher(pares, batch_size):
                tarefas = [
                    self._executor.submit(
                        self._processar_par, symbol, tf, plugins_analise, sinais_plugin, buffer_sinais
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
                        sinais_timeframes = buffer_sinais[symbol]
                        sinal_final = sinais_plugin.consolidar_sinais_multi_timeframe(
                            sinais_timeframes, symbol, self._config
                        )
                        logger.execution(f"Sinal consolidado multi-timeframe para {symbol}: {sinal_final}")

            logger.execution(f"Ciclo finalizado para todos os pares")
            return all(resultados_gerais)
        except Exception as e:
            logger.error(f"Erro geral no ciclo do bot: {e}", exc_info=True)
            return False

    def _processar_par(self, symbol, timeframe, plugins_analise, sinais_plugin, buffer_sinais=None) -> bool:
        """
        Processa um par/timeframe, executando plugins de análise e sinais.

        Args:
            symbol: Símbolo do par (ex.: BTCUSDT).
            timeframe: Timeframe (ex.: 1m).
            plugins_analise: Lista de plugins com tag 'analise'.
            sinais_plugin: Instância do plugin sinais_plugin.
            buffer_sinais: Buffer temporário para armazenar sinais por símbolo/timeframe.

        Returns:
            bool: True se o processamento foi bem-sucedido, False caso contrário.
        """
        try:
            logger.execution(f"Início do processamento: {symbol} - {timeframe}")
            dados = {}

            # Popula k-lines via plugin ObterDados antes das análises
            obter_dados = self._gerente.obter_plugin("obter_dados")
            if obter_dados:
                obter_dados.executar(dados_completos=dados, symbol=symbol, timeframe=timeframe)
            else:
                logger.warning(f"[{self.PLUGIN_NAME}] Plugin ObterDados não encontrado para {symbol}-{timeframe}")

            # Executa plugins de análise
            for plugin in plugins_analise:
                resultado = plugin.executar(dados_completos=dados, symbol=symbol, timeframe=timeframe)
                if not isinstance(resultado, bool) or not resultado:
                    logger.warning(f"Plugin {plugin.PLUGIN_NAME} falhou para {symbol}-{timeframe}")

            # Executa o analisador_mercado separado, após todos os plugins de análise
            analisador_mercado = self._gerente.obter_plugin("analisador_mercado")
            if not analisador_mercado:
                logger.error("Plugin 'analisador_mercado' não encontrado no registro de plugins.")
                return False
            logger.debug(f"[Pipeline] Executando analisador_mercado para {symbol} - {timeframe}")
            # Validação de candles mínimos para plugins que dependem disso
            candles = dados.get("candles")
            if candles is None or len(candles) < 30:
                logger.warning(f"Candles insuficientes para {symbol}-{timeframe}: {len(candles) if candles else 0}")
                return False
            sucesso_analise = analisador_mercado.executar(
                dados_completos=dados, symbol=symbol, timeframe=timeframe
            )
            logger.debug(f"[Pipeline] analisador_mercado finalizado para {symbol} - {timeframe} (sucesso={sucesso_analise})")
            if not isinstance(sucesso_analise, bool) or not sucesso_analise:
                logger.warning(f"analisador_mercado falhou ou retornou valor inválido: {symbol} - {timeframe}")
                return False

            if not sinais_plugin.executar(
                dados_completos=dados, symbol=symbol, timeframe=timeframe
            ):
                logger.warning(f"sinais_plugin falhou para {symbol} - {timeframe}")
                return False

            # Armazena o sinal retornado no buffer temporário
            if buffer_sinais is not None:
                buffer_sinais[symbol][timeframe] = dados.get("sinais", {})

            self._estado_ativo[symbol][timeframe] = {"timestamp": time()}
            logger.execution(f"Processamento concluído: {symbol} - {timeframe}")
            return True

        except Exception as e:
            logger.error(f"Erro crítico em {symbol}-{timeframe}: {e}", exc_info=True)
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
            logger.info("GerenciadorBot finalizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao finalizar GerenciadorBot: {e}")
            return False
