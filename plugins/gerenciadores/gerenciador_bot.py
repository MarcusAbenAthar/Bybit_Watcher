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
            plugins_analise = self._gerente.filtrar_por_tag("analise")
            sinais_plugin = self._gerente.obter_plugin("sinais_plugin")

            if not sinais_plugin:
                logger.error("Plugin sinais_plugin não encontrado")
                return False

            logger.execution(f"Iniciando ciclo para {len(pares)} pares")

            tarefas = [
                self._executor.submit(
                    self._processar_par, symbol, tf, plugins_analise, sinais_plugin
                )
                for symbol in pares
                for tf in timeframes
            ]

            resultados = [t.result() for t in as_completed(tarefas)]
            logger.execution(f"Ciclo finalizado para todos os pares")

            return all(resultados)
        except Exception as e:
            logger.error(f"Erro geral no ciclo do bot: {e}", exc_info=True)
            return False

    def _processar_par(self, symbol, timeframe, plugins_analise, sinais_plugin) -> bool:
        """
        Processa um par/timeframe, executando plugins de análise e sinais.

        Args:
            symbol: Símbolo do par (ex.: BTCUSDT).
            timeframe: Timeframe (ex.: 1m).
            plugins_analise: Lista de plugins com tag 'analise'.
            sinais_plugin: Instância do plugin sinais_plugin.

        Returns:
            bool: True se o processamento foi bem-sucedido, False caso contrário.
        """
        try:
            logger.execution(f"Início do processamento: {symbol} - {timeframe}")
            dados = {"crus": [], "processados": {}}

            for plugin in plugins_analise:
                try:
                    success = plugin.executar(
                        dados_completos=dados, symbol=symbol, timeframe=timeframe
                    )
                    if not isinstance(success, bool) or not success:
                        logger.warning(
                            f"{plugin.nome} falhou ou retornou valor inválido: {symbol} - {timeframe}"
                        )
                        return False
                except Exception as e:
                    logger.error(f"Erro no {plugin.nome}: {e}", exc_info=True)
                    return False

            if not sinais_plugin.executar(
                dados_completos=dados, symbol=symbol, timeframe=timeframe
            ):
                logger.warning(f"sinais_plugin falhou para {symbol} - {timeframe}")
                return False

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
