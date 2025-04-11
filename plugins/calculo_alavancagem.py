# Plugin para calcular alavancagem com base em volatilidade e confiança

from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class CalculoAlavancagem(Plugin):
    PLUGIN_NAME = "calculo_alavancagem"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "volatilidade", "alavancagem"]
    PLUGIN_PRIORIDADE = 85

    def __init__(self, gerente: GerenciadorPlugins):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "trading": {
                "alavancagem_maxima": 20,
                "alavancagem_minima": 3,
            }
        }
        logger.debug(f"{self.nome} inicializado")

    def calcular_alavancagem(
        self,
        crus,
        direcao=None,
        confianca=0.0,
        alavancagem_maxima=20,
        alavancagem_minima=3,
    ):
        try:
            dados_extraidos = self._extrair_dados(crus, [2, 3, 4])
            high_raw, low_raw, close_raw = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )

            def normalizar(valores):
                return np.array(
                    [
                        float(x.get("valor", x)) if isinstance(x, dict) else float(x)
                        for x in valores
                    ]
                )

            high = normalizar(high_raw)
            low = normalizar(low_raw)
            close = normalizar(close_raw)

            if len(close) < 14:
                logger.warning("Dados insuficientes para calcular ATR")
                return alavancagem_minima

            atr = talib.ATR(high, low, close, timeperiod=14)
            if not atr.size:
                return alavancagem_minima

            atr_atual = atr[-1]
            preco_atual = close[-1]
            volatilidade = atr_atual / preco_atual

            if volatilidade < 0.001:
                alav_base = 20
            elif volatilidade < 0.005:
                alav_base = 10
            else:
                alav_base = 5

            try:
                confianca = float(confianca)
            except (ValueError, TypeError):
                logger.warning(f"Confiança inválida: {confianca}, usando fallback 0.0")
                confianca = 0.0

            fator_conf = (confianca / 100) if confianca > 0 else 0.3
            alavancagem_final = alav_base * fator_conf

            if direcao == "NEUTRO":
                return alavancagem_minima

            return round(
                max(alavancagem_minima, min(alavancagem_final, alavancagem_maxima)), 2
            )

        except Exception as e:
            logger.error(f"Erro ao calcular alavancagem: {e}")
            return alavancagem_minima

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {"alavancagem": 3}
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            config = kwargs.get("config", self.config)

            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos em {self.nome}")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            klines = (
                dados_completos.get("crus", [])
                if isinstance(dados_completos, dict)
                else dados_completos
            )
            if not isinstance(klines, list) or len(klines) < 14:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados_completos, dict):
                    dados_completos.update(resultado_padrao)
                return True

            alavancagem = self.calcular_alavancagem(klines)
            if isinstance(dados_completos, dict):
                dados_completos["alavancagem"] = alavancagem
                logger.debug(
                    f"Alavancagem calculada para {symbol} - {timeframe}: {alavancagem}"
                )

            return True
        except Exception as e:
            logger.error(f"Erro ao executar {self.nome}: {e}")
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True
