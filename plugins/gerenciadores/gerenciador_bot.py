# gerenciador_bot.py
"""Gerenciador principal do bot de trading."""

from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class GerenciadorBot(Plugin):
    """Gerenciador central do bot."""

    PLUGIN_NAME = "gerenciador_bot"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente):
        """Inicializa o gerenciador com o gerente de plugins."""
        super().__init__()
        self._gerente = gerente  # Obrigatório, injetado pelo main.py
        self._status = "parado"

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o gerenciador com configurações.

        Args:
            config: Dicionário de configurações do bot

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if not super().inicializar(config):
                return False
            self._status = "iniciando"
            logger.info("GerenciadorBot inicializado")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar GerenciadorBot: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        try:
            if self._status != "rodando":
                logger.warning("Bot não está rodando, ciclo não executado")
                return False

            pares = self._config["pares"]
            timeframes = self._config["timeframes"]
            plugins_analise = [
                "plugins.conexao",
                "plugins.validador_dados",
                "plugins.indicadores.indicadores_tendencia",
                "plugins.medias_moveis",
                "plugins.calculo_alavancagem",
                "plugins.analise_candles",
                "plugins.price_action",
                "plugins.calculo_risco",
                "plugins.indicadores.indicadores_osciladores",
                "plugins.indicadores.indicadores_volatilidade",
                "plugins.indicadores.indicadores_volume",
                "plugins.indicadores.outros_indicadores",
                "plugins.analisador_mercado",
            ]

            for symbol in pares:
                logger.info(f"Análise iniciada para {symbol}")
                dados = {tf: {"crus": [], "processados": {}} for tf in timeframes}

                for tf in timeframes:
                    for plugin_name in plugins_analise:
                        plugin = self._gerente.obter_plugin(plugin_name)
                        if plugin:
                            plugin.executar(
                                dados_completos=dados[tf], symbol=symbol, timeframe=tf
                            )
                        else:
                            logger.warning(f"Plugin {plugin_name} não encontrado")

                    sinais_plugin = self._gerente.obter_plugin("plugins.sinais_plugin")
                    if sinais_plugin:
                        sinais_plugin.executar(dados=dados, symbol=symbol)
                    else:
                        logger.error("SinaisPlugin não encontrado")
                        return False

                logger.info(f"Análise concluída para {symbol}")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar ciclo: {e}")
            return False

    def iniciar(self) -> bool:
        """Inicia o bot."""
        try:
            self._status = "rodando"
            logger.info("Bot iniciado")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}")
            return False

    def parar(self) -> bool:
        """Para o bot."""
        try:
            self._status = "parado"
            logger.info("Bot parado")
            return True
        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}")
            return False
