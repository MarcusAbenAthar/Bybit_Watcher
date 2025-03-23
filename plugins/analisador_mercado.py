# analisador_mercado.py
from utils.logging_config import get_logger
from typing import Dict
from plugins.plugin import Plugin

logger = get_logger(__name__)


class AnalisadorMercado(Plugin):
    PLUGIN_NAME = "analisador_mercado"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerente=None):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

    def inicializar(self, config: Dict) -> bool:
        if not super().inicializar(config):
            return False
        plugins = {
            "conexao": "plugins.conexao",
            "sinais_plugin": "plugins.sinais_plugin",
            "analise_candles": "plugins.analise_candles",
            "medias_moveis": "plugins.medias_moveis",
            "price_action": "plugins.price_action",
            "indicadores_tendencia": "plugins.indicadores.indicadores_tendencia",
        }
        for attr, plugin_key in plugins.items():
            plugin = self._gerente.obter_plugin(plugin_key)
            if not plugin:
                logger.error(f"Plugin {plugin_key} não encontrado")
                return False
            setattr(self, f"_{attr}", plugin)
        return True

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "analise_mercado": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            config = kwargs.get("config", self._config)

            if not all([dados, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            if not isinstance(dados, dict):
                logger.warning(
                    f"Dados devem ser um dicionário para {symbol} - {timeframe}"
                )
                return True

            resultados = self._executar_analises(dados, symbol, timeframe, config)
            dados.update(resultados)
            return True
        except Exception as e:
            logger.error(f"Erro ao executar analisador_mercado: {e}")
            if isinstance(dados, dict):
                dados.update(resultado_padrao)
            return True

    def _executar_analises(
        self, dados: Dict, symbol: str, timeframe: str, config: Dict
    ) -> Dict:
        try:
            resultados = {}
            for plugin_name, plugin in [
                ("candles", self._analise_candles),
                ("medias_moveis", self._medias_moveis),
                ("price_action", self._price_action),
                ("tendencia", self._indicadores_tendencia),
            ]:
                plugin.executar(
                    dados=dados, symbol=symbol, timeframe=timeframe, config=config
                )
                resultados[plugin_name] = dados.get(
                    plugin_name,
                    {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
                )

            direcao, forca, confianca = self._consolidar_resultados(resultados)
            return {
                "analise_mercado": {
                    "direcao": direcao,
                    "forca": forca,
                    "confianca": confianca,
                }
            }
        except Exception as e:
            logger.error(f"Erro ao executar análises: {e}")
            return {
                "analise_mercado": {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                }
            }

    def _consolidar_resultados(self, resultados: Dict) -> tuple:
        try:
            direcoes = [r["direcao"] for r in resultados.values()]
            confiancas = [r["confianca"] for r in resultados.values()]
            total_confirmacoes = sum(1 for d in direcoes if d != "NEUTRO")
            if total_confirmacoes == 0:
                return "NEUTRO", "FRACA", 0.0

            direcao_predominante = max(set(direcoes), key=direcoes.count)
            if direcao_predominante == "NEUTRO":
                return "NEUTRO", "FRACA", 0.0

            confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0.0
            forca = (
                "FORTE"
                if total_confirmacoes >= 3
                else "MÉDIA" if total_confirmacoes == 2 else "FRACA"
            )
            return direcao_predominante, forca, confianca_media
        except Exception as e:
            logger.error(f"Erro ao consolidar resultados: {e}")
            return "NEUTRO", "FRACA", 0.0
