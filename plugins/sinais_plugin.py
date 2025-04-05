from utils.logging_config import get_logger
from utils.sinais_logging import SINAIS_LOGGING_CONFIG
from plugins.plugin import Plugin
import logging.config
import os

logger = get_logger(__name__)
logger.handlers = []  # Limpa handlers existentes
logger.addHandler(logging.StreamHandler())  # Adiciona apenas um
logger.info(
    f"Caminho absoluto do sinais_plugin.py: {os.path.abspath(__file__)}"
)  # Aparece no log


class SinaisPlugin(Plugin):
    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.plugins_analise = [
            "plugins.calculo_risco",
            "plugins.analise_candles",
            "plugins.medias_moveis",
            "plugins.price_action",
            "plugins.indicadores.indicadores_tendencia",
            "plugins.indicadores.indicadores_osciladores",
            "plugins.indicadores.indicadores_volatilidade",
            "plugins.indicadores.indicadores_volume",
            "plugins.indicadores.outros_indicadores",
            "plugins.analisador_mercado",
        ]

    def inicializar(self, config: dict) -> bool:
        if not super().inicializar(config):
            return False
        try:
            logging.config.dictConfig(SINAIS_LOGGING_CONFIG)
            logger.info("SinaisPlugin inicializado com config: %s", config)
            return True
        except Exception as e:
            logger.error("Erro ao inicializar SinaisPlugin: %s", e)
            return False

    def executar(self, *args, **kwargs) -> bool:
        symbol = kwargs.get("symbol", "BTCUSDT")
        timeframe = kwargs.get("timeframe", "1m")
        logger.execution(f"SinaisPlugin processando {symbol} - {timeframe}")
        logger.debug(f"Iniciando execução do SinaisPlugin para {symbol} - {timeframe}")
        dados_completos = kwargs.get("dados_completos", {})
        config = kwargs.get("config", self._config)

        logger.debug(f"Dados recebidos: {dados_completos}")
        logger.debug(
            f"Plugins disponíveis no gerente: {list(self._gerente.plugins.keys())}"
        )
        logger.debug(
            f"Configuração atual: {self._config}"
        )  # Adicionado pra verificar o config

        resultado_padrao = {
            "sinais": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
            }
        }
        if not dados_completos or not symbol or not timeframe:
            logger.error(
                f"Parâmetros necessários não fornecidos: dados_completos={bool(dados_completos)}, symbol={symbol}, timeframe={timeframe}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return False

        if not isinstance(dados_completos, dict) or "crus" not in dados_completos:
            logger.warning(
                f"Dados inválidos para {symbol} - {timeframe}: dados_completos é dict={isinstance(dados_completos, dict)}, contém 'crus'={'crus' in dados_completos}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return False

        try:
            logger.debug(
                f"Executando plugins de análise para {symbol} - {timeframe}: {self.plugins_analise}"
            )
            for plugin_name in self.plugins_analise:
                if plugin_name in self._gerente.plugins:
                    logger.debug(f"Executando plugin {plugin_name}")
                    plugin = self._gerente.obter_plugin(plugin_name)
                    if plugin:
                        sucesso = plugin.executar(
                            dados_completos=dados_completos,
                            symbol=symbol,
                            timeframe=timeframe,
                            config=config,
                        )
                        if not sucesso:
                            logger.warning(
                                f"Plugin {plugin_name} falhou para {symbol} - {timeframe}"
                            )
                            logger.error(
                                f"Abortando execução devido à falha do plugin {plugin_name}"
                            )
                            if isinstance(dados_completos, dict):
                                dados_completos.update(resultado_padrao)
                            return False
                        else:
                            logger.debug(
                                f"Plugin {plugin_name} executado com sucesso: {dados_completos.get(plugin_name.split('.')[-1], 'N/A')}"
                            )
                    else:
                        logger.error(
                            f"Plugin {plugin_name} retornou None ao ser obtido"
                        )
                        if isinstance(dados_completos, dict):
                            dados_completos.update(resultado_padrao)
                        return False
                else:
                    logger.error(f"Plugin {plugin_name} não encontrado no gerenciador")
                    if isinstance(dados_completos, dict):
                        dados_completos.update(resultado_padrao)
                    return False

            logger.debug(f"Chamando _consolidar_sinais para {symbol} - {timeframe}")
            sinais = self._consolidar_sinais(dados_completos, symbol, timeframe)
            logger.debug(f"Sinais calculados para {symbol} - {timeframe}: {sinais}")
            dados_completos["sinais"] = sinais
            logger.execution(f"Sinais consolidados para {symbol} - {timeframe}")
            logger.info(f"Sinal consolidado para {symbol} - {timeframe}: {sinais}")
            logger.debug(f"Execução concluída com sucesso para {symbol} - {timeframe}")
            return True

        except Exception as e:
            logger.error(
                f"Erro ao executar SinaisPlugin para {symbol} - {timeframe}: {str(e)}",
                exc_info=True,
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return False

    def _consolidar_sinais(
        self, dados_completos: dict, symbol: str, timeframe: str
    ) -> dict:
        try:
            logger.debug(f"Consolidando sinais para {symbol} - {timeframe}")
            analise_mercado = dados_completos.get(
                "analise_mercado",
                {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
            )

            resultados = {
                "calculo_risco": dados_completos.get(
                    "calculo_risco", {"confianca": 0.0}
                ),
                "analise_candles": dados_completos.get("candles", {"confianca": 0.0}),
                "medias_moveis": dados_completos.get(
                    "medias_moveis", {"confianca": 0.0}
                ),
                "price_action": dados_completos.get("price_action", {"confianca": 0.0}),
                "indicadores_tendencia": dados_completos.get(
                    "tendencia", {"confianca": 0.0}
                ),
                "indicadores_osciladores": dados_completos.get(
                    "osciladores", {"confianca": 0.0}
                ),
                "indicadores_volatilidade": dados_completos.get(
                    "volatilidade", {"confianca": 0.0}
                ),
                "indicadores_volume": dados_completos.get("volume", {"confianca": 0.0}),
                "outros_indicadores": dados_completos.get("outros", {"confianca": 0.0}),
            }

            direcao = analise_mercado["direcao"]
            forca = analise_mercado["forca"]
            confianca_base = analise_mercado["confianca"]

            confiancas = [
                r["confianca"]
                for r in resultados.values()
                if r.get("confianca", 0.0) > 0
            ]
            confianca = confianca_base
            if confiancas:
                confianca_media = sum(confiancas) / len(confiancas)
                confianca = (confianca_base + confianca_media) / 2
                for nome, res in resultados.items():
                    if res.get("direcao") == direcao and res.get("confianca", 0.0) > 0:
                        confianca += 5.0
                    elif (
                        res.get("direcao") not in [direcao, "NEUTRO"]
                        and res.get("confianca", 0.0) > 0
                    ):
                        confianca -= 5.0

            confianca = max(0.0, min(confianca, 100.0))
            logger.debug(f"Confiança calculada: {confianca}")

            calc_alavancagem = self._gerente.obter_plugin("plugins.calculo_alavancagem")
            if not calc_alavancagem:
                logger.error("Plugin calculo_alavancagem não encontrado")
                alavancagem = 0.0
            else:
                logger.debug(f"Config trading: {self._config.get('trading', 'N/A')}")
                alavancagem = calc_alavancagem.calcular_alavancagem(
                    dados_completos["crus"],
                    direcao=direcao,
                    confianca=confianca,
                    alavancagem_maxima=self._config["trading"]["alavancagem_maxima"],
                    alavancagem_minima=self._config["trading"]["alavancagem_minima"],
                )
                logger.debug(f"Alavancagem calculada: {alavancagem}")

            timestamp = (
                dados_completos["crus"][-1][0] if dados_completos["crus"] else None
            )

            sinais = {
                "direcao": direcao,
                "forca": forca,
                "confianca": round(confianca, 2),
                "alavancagem": alavancagem,
                "timestamp": timestamp,
            }
            logger.debug(f"Consolidação concluída: {sinais}")
            return sinais
        except Exception as e:
            logger.error(f"Erro ao consolidar sinais: {str(e)}", exc_info=True)
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
            }
