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
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")

            if not all([dados, symbol]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados.update(resultado_padrao)
                return True

            if not isinstance(dados, dict):
                logger.warning(f"Dados devem ser um dicionário para {symbol}")
                return True

            timeframes = self._config.get(
                "timeframes", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
            )
            sinais_por_timeframe = self._gerar_sinais_por_timeframe(
                dados, symbol, timeframes
            )
            sinal_consolidado = self._consolidar_sinais(sinais_por_timeframe, symbol)

            if sinal_consolidado and self._validar_sinal(sinal_consolidado):
                logger.info(
                    f"Sinal consolidado válido para {symbol}: {sinal_consolidado}"
                )
                dados["sinais"] = sinal_consolidado
            else:
                logger.debug(f"Sinal consolidado inválido ou neutro para {symbol}")
                dados["sinais"] = None
            return True
        except Exception as e:
            logger.error(f"Erro ao executar sinais_plugin: {e}")
            if isinstance(dados, dict):
                dados.update(resultado_padrao)
            return True

    def _gerar_sinais_por_timeframe(self, dados, symbol, timeframes):
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
        sinais = {}
        for tf in timeframes:
            if tf not in dados:
                sinais[tf] = {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 3,
                }
                continue
            indicadores = {}
            confianca_total = 0
            alavancagem = dados[tf].get("calculo_alavancagem", 3)
            for plugin in plugins_analise:
                resultado = dados[tf].get(
                    plugin, {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
                )
                indicadores[plugin] = resultado
                confianca_total += resultado["confianca"]
            confianca = (
                confianca_total / len(plugins_analise) if plugins_analise else 0.0
            )
            sinais[tf] = {
                "direcao": indicadores.get("calculo_risco", {}).get(
                    "direcao", "NEUTRO"
                ),
                "forca": "MÉDIA",
                "confianca": confianca,
                "alavancagem": alavancagem,
                "indicadores": indicadores,
            }
        return sinais

    def _consolidar_sinais(self, sinais, symbol):
        try:
            direcao = self._determinar_direcao(sinais)
            forca = self._calcular_forca(sinais)
            confianca = self._calcular_confianca(sinais)
            alavancagem = self._calcular_alavancagem(sinais)
            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "alavancagem": alavancagem,
                "indicadores": sinais,
            }
        except Exception as e:
            logger.error(f"Erro ao consolidar sinais para {symbol}: {e}")
            return None

    def _determinar_direcao(self, sinais):
        pesos = {
            "1m": 1.0,
            "5m": 0.95,
            "15m": 0.9,
            "30m": 0.85,
            "1h": 0.8,
            "4h": 0.7,
            "1d": 0.6,
        }
        alta, baixa, total = 0, 0, 0
        for tf, sinal in sinais.items():
            peso = pesos.get(tf, 1.0)
            total += peso
            if sinal["direcao"] == "ALTA":
                alta += peso
            elif sinal["direcao"] == "BAIXA":
                baixa += peso
        return (
            "ALTA"
            if alta / total >= 0.6
            else "BAIXA" if baixa / total >= 0.6 else "NEUTRO"
        )

    def _calcular_forca(self, sinais):
        pesos = {
            "1m": 1.0,
            "5m": 0.95,
            "15m": 0.9,
            "30m": 0.85,
            "1h": 0.8,
            "4h": 0.7,
            "1d": 0.6,
        }
        forca_total, total = 0, 0
        for tf, sinal in sinais.items():
            peso = pesos.get(tf, 1.0)
            total += peso
            forca_total += peso * (
                3
                if sinal["forca"] == "FORTE"
                else 2 if sinal["forca"] == "MÉDIA" else 1
            )
        media = (forca_total / (total * 3)) * 100 if total > 0 else 0
        return "FORTE" if media >= 85 else "MÉDIA" if media >= 40 else "FRACA"

    def _calcular_confianca(self, sinais):
        pesos = {
            "1m": 1.0,
            "5m": 0.95,
            "15m": 0.9,
            "30m": 0.85,
            "1h": 0.8,
            "4h": 0.7,
            "1d": 0.6,
        }
        confianca_total, total = 0, 0
        for tf, sinal in sinais.items():
            peso = pesos.get(tf, 1.0)
            total += peso
            confianca_total += sinal["confianca"] * peso
        return confianca_total / total if total > 0 else 0.0

    def _calcular_alavancagem(self, sinais):
        pesos = {
            "1m": 1.0,
            "5m": 0.95,
            "15m": 0.9,
            "30m": 0.85,
            "1h": 0.8,
            "4h": 0.7,
            "1d": 0.6,
        }
        alavancagem_total, total = 0, 0
        for tf, sinal in sinais.items():
            peso = pesos.get(tf, 1.0)
            total += peso
            alavancagem_total += sinal["alavancagem"] * peso
        return int(alavancagem_total / total) if total > 0 else 3

    def _validar_sinal(self, sinal):
        return sinal["direcao"] != "NEUTRO" and sinal["confianca"] >= 80
