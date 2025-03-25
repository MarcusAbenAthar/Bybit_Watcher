# sinais_plugin.py
from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class SinaisPlugin(Plugin):
    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_TYPE = "essencial"

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {"sinais": None}
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            if not isinstance(dados_completos, dict):
                logger.warning(
                    f"Dados devem ser um dicionário para {symbol} - {timeframe}"
                )
                return True

            # Gerar sinal para o timeframe atual
            sinal = self._gerar_sinal_para_timeframe(dados_completos, symbol, timeframe)
            if sinal and self._validar_sinal(sinal):
                logger.info(f"Sinal válido para {symbol} - {timeframe}: {sinal}")
                dados_completos["sinais"] = sinal
            else:
                logger.debug(f"Sinal inválido ou neutro para {symbol} - {timeframe}")
                dados_completos["sinais"] = None
            return True
        except Exception as e:
            logger.error(f"Erro ao executar sinais_plugin: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

    def _gerar_sinal_para_timeframe(self, dados_completos, symbol, timeframe):
        plugins_analise = [
            "indicadores_tendencia",
            "medias_moveis",
            "analise_candles",
            "price_action",
            "calculo_risco",
            "indicadores_osciladores",
            "indicadores_volatilidade",
            "indicadores_volume",
            "outros_indicadores",
            "analisador_mercado",
        ]
        indicadores = {}
        confianca_total = 0
        alavancagem = dados_completos.get(
            "calculo_alavancagem", 3
        )  # Valor padrão se não houver

        # Coletar resultados dos plugins de análise
        for plugin in plugins_analise:
            resultado = dados_completos.get("processados", {}).get(
                plugin, {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
            )
            indicadores[plugin] = resultado
            confianca_total += resultado["confianca"]

        confianca = confianca_total / len(plugins_analise) if plugins_analise else 0.0
        direcao = indicadores.get("calculo_risco", {}).get("direcao", "NEUTRO")
        forca = "MÉDIA"  # Pode ser ajustado conforme lógica adicional

        return {
            "direcao": direcao,
            "forca": forca,
            "confianca": confianca,
            "alavancagem": alavancagem,
            "indicadores": indicadores,
        }

    def _validar_sinal(self, sinal):
        return sinal["direcao"] != "NEUTRO" and sinal["confianca"] >= 80
