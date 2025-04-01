# calculo_alavancagem.py
# Plugin para calcular alavancagem com base em volatilidade e timeframe

from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class CalculoAlavancagem(Plugin):
    PLUGIN_NAME = "calculo_alavancagem"
    PLUGIN_TYPE = "analise"

    def __init__(self, gerente: GerentePlugin):
        super().__init__(gerente=gerente)
        self._gerente = gerente
        self.config = {
            "trading": {
                "alavancagem_maxima": 20,
                "alavancagem_minima": 3,
            }
        }
        logger.debug(f"{self.nome} inicializado")

    def _extrair_dados(self, dados_completos, indices):
        try:
            valores = {idx: [] for idx in indices}
            for candle in dados_completos:
                if any(
                    candle[i] is None or str(candle[i]).strip() == "" for i in indices
                ):
                    continue
                try:
                    for idx in indices:
                        valor = float(
                            str(candle[idx]).replace("e", "").replace("E", "")
                        )
                        valores[idx].append(valor)
                except (ValueError, TypeError):
                    continue
            if not all(valores.values()):
                logger.warning(f"Dados insuficientes ou inválidos em {self.nome}")
                return {idx: np.array([]) for idx in indices}
            return {idx: np.array(valores[idx], dtype=np.float64) for idx in indices}
        except Exception as e:
            logger.error(f"Erro ao extrair dados em {self.nome}: {e}")
            return {idx: np.array([]) for idx in indices}

    def calcular_alavancagem(self, dados_completos, symbol, timeframe, config):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(close) < 14:
                logger.warning(f"Dados insuficientes para calcular ATR: {len(close)}")
                return 3

            atr = talib.ATR(high, low, close, timeperiod=14)
            if not atr.size:
                return 3

            atr_atual = atr[-1]
            preco_atual = float(close[-1])
            volatilidade = atr_atual / preco_atual

            trading_config = config.get("trading", {})
            alavancagem_maxima = int(trading_config.get("alavancagem_maxima", 20))
            alavancagem_minima = int(trading_config.get("alavancagem_minima", 3))

            if volatilidade < 0.001:
                alavancagem_base = int(20 - (volatilidade * 10000))
            elif volatilidade < 0.005:
                alavancagem_base = int(10 - (volatilidade - 0.001) * 1250)
            else:
                alavancagem_base = int(5 - (volatilidade - 0.005) * 100)

            timeframe_pesos = {
                "1m": 1.0,
                "5m": 0.95,
                "15m": 0.9,
                "30m": 0.85,
                "1h": 0.8,
                "4h": 0.7,
                "1d": 0.6,
            }
            peso = timeframe_pesos.get(timeframe, 1.0)
            alavancagem_ajustada = int(alavancagem_base / peso)

            return max(
                alavancagem_minima, min(alavancagem_ajustada, alavancagem_maxima)
            )
        except Exception as e:
            logger.error(f"Erro ao calcular alavancagem: {e}")
            return 3

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

            alavancagem = self.calcular_alavancagem(klines, symbol, timeframe, config)
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
