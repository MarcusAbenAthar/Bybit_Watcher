from utils.logging_config import get_logger
from utils.sinais_logging import SINAIS_LOGGING_CONFIG
from plugins.plugin import Plugin
import logging.config

logger = get_logger(__name__)


class SinaisPlugin(Plugin):
    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.plugins_analise = [
            "calculo_risco",
            "analise_candles",
            "medias_moveis",
            "price_action",
            "indicadores_tendencia",
            "indicadores_osciladores",
            "indicadores_volatilidade",
            "indicadores_volume",
            "outros_indicadores",
            "analisador_mercado",
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
        resultado_padrao = {
            "sinais": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
            }
        }

        dados_completos = kwargs.get("dados_completos", {})
        config = kwargs.get("config", self._config)

        if not dados_completos or not symbol or not timeframe:
            logger.error(
                f"Parâmetros necessários não fornecidos: dados_completos={bool(dados_completos)}, symbol={symbol}, timeframe={timeframe}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        if not isinstance(dados_completos, dict) or "crus" not in dados_completos:
            logger.warning(
                f"Dados inválidos para {symbol} - {timeframe}: dados_completos é dict={isinstance(dados_completos, dict)}, contém 'crus'={'crus' in dados_completos}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        try:
            logger.debug(
                f"Executando plugins de análise para {symbol} - {timeframe}: {self.plugins_analise}"
            )
            for plugin_name in self.plugins_analise:
                if plugin_name in self._gerente.plugins:
                    logger.debug(f"Executando plugin {plugin_name}")
                    sucesso = self._gerente.executar_plugin(
                        plugin_name,
                        dados_completos=dados_completos,
                        symbol=symbol,
                        timeframe=timeframe,
                        config=config,
                    )
                    if not sucesso:
                        logger.warning(
                            f"Plugin {plugin_name} falhou para {symbol} - {timeframe}"
                        )

            sinais = self._consolidar_sinais(dados_completos, symbol, timeframe)
            logger.debug(f"Sinais calculados para {symbol} - {timeframe}: {sinais}")
            dados_completos["sinais"] = sinais
            logger.execution(f"Sinais consolidados para {symbol} - {timeframe}")
            logger.info(f"Sinal consolidado para {symbol} - {timeframe}: {sinais}")
            return True

        except Exception as e:
            logger.error(
                f"Erro ao executar SinaisPlugin para {symbol} - {timeframe}: {e}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _consolidar_sinais(
        self, dados_completos: dict, symbol: str, timeframe: str
    ) -> dict:
        try:
            analise_mercado = dados_completos.get(
                "analise_mercado",
                {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
            )

            resultados = {
                "calculo_risco": dados_completos.get(
                    "calculo_risco", {"confianca": 0.0}
                ),
                "candles": dados_completos.get("candles", {"confianca": 0.0}),
                "medias_moveis": dados_completos.get(
                    "medias_moveis", {"confianca": 0.0}
                ),
                "price_action": dados_completos.get("price_action", {"confianca": 0.0}),
                "tendencia": dados_completos.get("tendencia", {"confianca": 0.0}),
                "osciladores": dados_completos.get("osciladores", {"confianca": 0.0}),
                "volatilidade": dados_completos.get("volatilidade", {"confianca": 0.0}),
                "volume": dados_completos.get("volume", {"confianca": 0.0}),
                "outros": dados_completos.get("outros", {"confianca": 0.0}),
            }

            direcao = analise_mercado["direcao"]
            forca = analise_mercado["forca"]

            confiancas = [
                r["confianca"]
                for r in resultados.values()
                if r.get("confianca", 0.0) > 0
            ]
            confianca = (
                sum(confiancas) / len(confiancas)
                if confiancas
                else analise_mercado["confianca"]
            )

            calc_alavancagem = self._gerente.obter_plugin("plugins.calculo_alavancagem")
            if not calc_alavancagem:
                logger.error("Plugin calculo_alavancagem não encontrado")
                alavancagem = 0
            else:
                alavancagem = calc_alavancagem.calcular_alavancagem(
                    dados_completos["crus"],
                    direcao=direcao,
                    confianca=confianca,
                    alavancagem_maxima=self._config["trading"]["alavancagem_maxima"],
                    alavancagem_minima=self._config["trading"]["alavancagem_minima"],
                )

            timestamp = (
                dados_completos["crus"][-1][0] if dados_completos["crus"] else None
            )

            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": round(confianca, 2),
                "alavancagem": alavancagem,
                "timestamp": timestamp,
            }
        except Exception as e:
            logger.error(f"Erro ao consolidar sinais: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
            }
