"""Gerenciador principal do bot de trading - versão inteligente com paralelismo."""

from utils.logging_config import get_logger
from plugins.gerenciadores.gerenciadores import BaseGerenciador
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from time import time

logger = get_logger(__name__)


class GerenciadorBot(BaseGerenciador):
    """Gerenciador central e inteligente do bot."""

    PLUGIN_NAME = "gerenciador_bot"
    PLUGIN_CATEGORIA = "gerenciador"
    PLUGIN_TAGS = ["core", "controle"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._status = "parado"
        self._executor = ThreadPoolExecutor(max_workers=4)  # Ajustável
        self._estado_ativo = defaultdict(dict)  # Guarda status por par-timeframe

    def inicializar(self, config: dict) -> bool:
        try:
            self._config = config
            self.inicializado = True
            self._status = "iniciando"
            logger.info("GerenciadorBot inicializado")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar GerenciadorBot: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> bool:
        if self._status != "rodando":
            logger.warning("Bot não está rodando")
            return False

        try:
            pares = self._config["pares"]
            timeframes = self._config["timeframes"]
            plugins_analise = self._gerente.filtrar_por_tag("analise")
            sinais_plugin = self._gerente.obter_plugin("sinais_plugin")

            if not sinais_plugin:
                logger.error("Plugin sinais_plugin não encontrado")
                return False

            logger.execution(f"Iniciando ciclo para {len(pares)} pares")

            tarefas = []
            for symbol in pares:
                for tf in timeframes:
                    tarefas.append(
                        self._executor.submit(
                            self._processar_par,
                            symbol,
                            tf,
                            plugins_analise,
                            sinais_plugin,
                        )
                    )

            resultados = [t.result() for t in as_completed(tarefas)]
            logger.execution(f"Ciclo finalizado para todos os pares")

            return all(resultados)
        except Exception as e:
            logger.error(f"Erro geral no ciclo do bot: {e}", exc_info=True)
            return False

    def _processar_par(self, symbol, timeframe, plugins_analise, sinais_plugin) -> bool:
        try:
            logger.execution(f"Início do processamento: {symbol} - {timeframe}")
            dados = {"crus": [], "processados": {}}

            for plugin in plugins_analise:
                try:
                    success = plugin.executar(
                        dados_completos=dados,
                        symbol=symbol,
                        timeframe=timeframe,
                    )
                    if not success:
                        logger.warning(f"{plugin.nome} falhou: {symbol} - {timeframe}")
                except Exception as e:
                    logger.error(f"Erro no {plugin.nome}: {e}", exc_info=True)

            success = sinais_plugin.executar(
                dados_completos=dados,
                symbol=symbol,
                timeframe=timeframe,
            )

            if not success:
                logger.warning(f"sinais_plugin falhou para {symbol} - {timeframe}")
                return False

            self._estado_ativo[symbol][timeframe] = {"timestamp": time()}
            logger.execution(f"Processamento concluído: {symbol} - {timeframe}")
            return True

        except Exception as e:
            logger.error(f"Erro crítico em {symbol}-{timeframe}: {e}", exc_info=True)
            return False

    def iniciar(self) -> bool:
        try:
            self._status = "rodando"
            logger.info("Bot em execução")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}", exc_info=True)
            return False

    def parar(self) -> bool:
        try:
            self._status = "parado"
            logger.info("Bot pausado")
            return True
        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}", exc_info=True)
            return False
