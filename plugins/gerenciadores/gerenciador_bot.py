# gerenciador_bot.py
# Gerenciador principal do bot.

"""
Gerenciador principal do bot.

Regras de Ouro:
1. Autonomo - Decisões automáticas
2. Criterioso - Validações rigorosas
3. Seguro - Tratamento de erros
4. Certeiro - Análises precisas
5. Eficiente - Otimizado
6. Clareza - Bem documentado
7. Modular - Responsabilidade única
8. Plugins - Interface padronizada
9. Testável - Métodos isolados
10. Documentado - Docstrings completos
"""

from utils.logging_config import get_logger

logger = get_logger(__name__)
from typing import Dict, List, Optional
from plugins.plugin import Plugin


class GerenciadorBot(Plugin):
    """
    Gerenciador central do bot.

    Responsável por:
    - Coordenar execução dos plugins
    - Gerenciar ciclo de vida do bot
    - Validar dados e resultados
    """

    # Identificadores do plugin
    PLUGIN_NAME = "gerenciador_bot"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o gerenciador."""
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.descricao = "Gerenciamento central do bot"
        self._config = None
        self._status = "parado"
        self.timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        self._plugins_ativos: Dict[str, Plugin] = {}
        self.inicializado = False

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o gerenciador.

        Args:
            config: Configurações do bot

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if self.inicializado:
                return True

            # Inicializa classe base primeiro
            if not super().inicializar(config):
                return False

            self._config = config
            self._status = "iniciando"

            # Só marca como inicializado se tudo der certo
            self.inicializado = True
            logger.info(f"Plugin {self.PLUGIN_NAME} inicializado")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciador: {e}")
            return False

    def registrar_plugin(self, plugin: Plugin) -> bool:
        """
        Registra um plugin para uso.

        Args:
            plugin: Plugin a ser registrado

        Returns:
            bool: True se registrado com sucesso
        """
        try:
            if not plugin.inicializado:
                logger.error(f"Plugin {plugin.PLUGIN_NAME} não inicializado")
                return False

            # Gera chave consistente para o plugin
            plugin_key = f"plugins.{plugin.PLUGIN_NAME}"
            self._plugins_ativos[plugin_key] = plugin
            logger.info(f"Plugin {plugin_key} registrado")
            return True

        except Exception as e:
            logger.error(f"Erro ao registrar plugin {plugin.PLUGIN_NAME}: {e}")
            return False

    def _validar_plugins_essenciais(self) -> bool:
        """
        Valida se todos os plugins essenciais estão registrados e ativos.

        Returns:
            bool: True se todos os plugins essenciais estão ok
        """
        plugins_essenciais = {
            "plugins.conexao": "Conexão com a Bybit",
            "plugins.gerenciador_banco": "Gerenciador do Banco",
            "plugins.banco_dados": "Banco de Dados",
            "plugins.sinais_plugin": "Gerador de Sinais",
        }

        for nome, descricao in plugins_essenciais.items():
            if nome not in self._plugins_ativos:
                logger.error(f"Plugin essencial faltando: {descricao} ({nome})")
                return False

            if not self._plugins_ativos[nome].inicializado:
                logger.error(f"Plugin não inicializado: {descricao} ({nome})")
                return False

        return True

    def obter_plugin(self, nome_plugin: str) -> Optional[Plugin]:
        """
        Obtém um plugin registrado.

        Args:
            nome_plugin: Nome do plugin

        Returns:
            Optional[Plugin]: Plugin ou None se não encontrado
        """
        return self._plugins_ativos.get(nome_plugin)

    def executar_ciclo(self, par: str = "BTCUSDT", timeframe: str = "1h") -> Dict:
        """
        Executa um ciclo completo de análise técnica para um par de negociação em todos os timeframes configurados.

        Coordena a execução ordenada de plugins para coletar, validar e processar dados de mercado, retornando
        sinais de análise técnica. É autônomo (não executa trades), criterioso (valida dados), seguro (trata exceções),
        eficiente (processa múltiplos timeframes), claro (logs detalhados), modular (baseado em plugins) e testável
        (retorna resultados estruturados).

        Args:
            par (str, optional): Par de negociação a ser analisado (ex.: "BTCUSDT"). Padrão é "BTCUSDT".
            timeframe (str, optional): Intervalo de tempo de fallback (ex.: "1h"). Ignorado se "timeframes"
                estiver configurado no config.

        Returns:
            Dict: Resultados no formato {par: {timeframe: dados_processados}}, com OHLCV, indicadores e sinais.
                Retorna vazio em caso de erro.

        Raises:
            Exception: Erros gerais são capturados e registrados no log.
        """
        try:
            # Verifica inicialização
            if not self.inicializado:
                logger.error("Gerenciador não inicializado. Ciclo abortado.")
                return {}

            resultados = {}

            # Verifica gerente de plugins
            if not hasattr(self, "gerente") or not self.gerente:
                logger.error("Gerente de plugins não fornecido ao GerenciadorBot.")
                return {}

            # Carrega configuração
            config_dict = self._config if self._config else {}
            config_dict.setdefault(
                "medias_moveis", {"mma_curta": 9, "mma_media": 21, "mma_longa": 50}
            )
            pares_config = config_dict.get("pares", par)

            # Determina pares
            if isinstance(pares_config, str) and pares_config.lower() == "all":
                conexao = self.gerente.plugins.get("plugins.conexao")
                if not conexao:
                    logger.error(
                        "Plugin 'plugins.conexao' não encontrado. Usando par padrão."
                    )
                    pares = [par]
                else:
                    pares = conexao.obter_pares_usdt()
            else:
                pares = (
                    pares_config.split(",") if isinstance(pares_config, str) else [par]
                )

            # Define timeframes
            timeframes = config_dict.get(
                "timeframes", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
            )

            # Ordem dos plugins
            plugins_ordem = [
                "plugins.conexao",
                "plugins.validador_dados",
                "plugins.indicadores.indicadores_tendencia",
                "plugins.medias_moveis",
                "plugins.calculo_alavancagem",
                "plugins.sinais_plugin",
            ]

            for par_iter in pares:
                resultados[par_iter] = {}
                for tf in timeframes:
                    # Log inicial para cada timeframe com contexto único
                    logger.info(
                        f"Iniciando análise para {par_iter} - {tf}",
                        extra={"par": par_iter, "tf": tf},
                    )
                    dados_completos = {"crus": [], "processados": {}}

                    for nome_plugin in plugins_ordem:
                        plugin = self.gerente.plugins.get(nome_plugin)
                        if not plugin:
                            logger.warning(
                                f"Plugin {nome_plugin} não encontrado para {par_iter} - {tf}."
                            )
                            continue

                        logger.debug(f"Executando {nome_plugin} para {par_iter} - {tf}")
                        kwargs = {
                            "dados_completos": dados_completos,
                            "symbol": par_iter.strip(),
                            "timeframe": tf.strip(),
                            "config": config_dict,
                        }
                        # Log opcional para depuração detalhada (removido do log atual)
                        # logger.debug(f"Dados completos antes de {nome_plugin}: {dados_completos}")
                        sucesso = plugin.executar(**kwargs)
                        if not sucesso:
                            logger.warning(
                                f"Falha ao executar {nome_plugin} para {par_iter} - {tf}."
                            )
                            continue
                        resultados[par_iter][tf] = dados_completos["processados"]

            return resultados
        except Exception as e:
            logger.error(f"Erro no ciclo de execução: {e}")
            return {}

    def esta_rodando(self) -> bool:
        """
        Verifica se o bot está em execução.

        Returns:
            bool: True se o bot está rodando
        """
        return self._status == "rodando"

    def iniciar(self) -> bool:
        """
        Inicia execução do bot.

        Returns:
            bool: True se iniciado com sucesso
        """
        try:
            if not self.inicializado:
                logger.error("Gerenciador não inicializado")
                return False

            if not self._validar_plugins_essenciais():
                logger.error("Plugins essenciais não validados")
                return False

            self._status = "rodando"
            logger.info("Bot iniciado")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}")
            return False

    def parar(self) -> bool:
        """
        Para execução do bot.

        Returns:
            bool: True se parado com sucesso
        """
        try:
            self._status = "parado"
            logger.info("Bot parado")
            return True

        except Exception as e:
            logger.error(f"Erro ao parar bot: {e}")
            return False

    def finalizar(self):
        """Finaliza o gerenciador."""
        try:
            self.parar()
            self._plugins_ativos.clear()
            logger.info("Gerenciador finalizado")

        except Exception as e:
            logger.error(f"Erro ao finalizar gerenciador: {e}")
