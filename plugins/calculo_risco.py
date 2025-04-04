# calculo_risco.py
from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class CalculoRisco(Plugin):
    PLUGIN_NAME = "calculo_risco"
    PLUGIN_TYPE = "essencial"

    def executar(self, *args, **kwargs) -> bool:
        logger.debug(
            f"Iniciando execução do CalculoRisco para {kwargs.get('symbol')} - {kwargs.get('timeframe')}"
        )
        resultado_padrao = {
            "calculo_risco": {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {},
            }
        }

        # Obter parâmetros com valores padrão
        dados_completos = kwargs.get("dados_completos", {})
        symbol = kwargs.get("symbol", "BTCUSDT")
        timeframe = kwargs.get("timeframe", "1m")
        min_klines = 50  # Requisito mínimo de klines

        # Validação inicial dos parâmetros
        if not dados_completos or not symbol or not timeframe:
            logger.error(
                f"Parâmetros necessários não fornecidos: dados_completos={bool(dados_completos)}, symbol={symbol}, timeframe={timeframe}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        # Verificar se dados_completos é um dicionário e contém klines suficientes
        if not isinstance(dados_completos, dict) or "crus" not in dados_completos:
            logger.warning(
                f"Dados inválidos para {symbol} - {timeframe}: dados_completos não é dict ou não contém 'crus'"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        klines = dados_completos.get("crus", [])
        if len(klines) < min_klines:
            logger.warning(
                f"Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines, mínimo necessário: {min_klines}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

        try:
            # Gerar sinal de cálculo de risco
            sinal = self.gerar_sinal(klines)
            logger.debug(
                f"Sinal de CalculoRisco gerado para {symbol} - {timeframe}: {sinal}"
            )
            dados_completos["calculo_risco"] = sinal
            logger.info(f"CalculoRisco concluído para {symbol} - {timeframe}: {sinal}")
            return True
        except Exception as e:
            logger.error(
                f"Erro ao executar CalculoRisco para {symbol} - {timeframe}: {e}"
            )
            if isinstance(dados_completos, dict):
                dados_completos.update(resultado_padrao)
            return True

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

    def gerar_sinal(self, dados_completos):
        try:
            dados_extraidos = self._extrair_dados(dados_completos, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(close) < 50:
                return {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "indicadores": {},
                }

            sinal = {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {
                    "tendencia": self._confirmar_tendencia(close),
                    "volatilidade": self._verificar_volatilidade(high, low, close),
                    "momentum": self._calcular_momentum(close),
                    "volume": self._verificar_volume(volume),
                },
            }

            if sinal["indicadores"]["tendencia"]:
                sinal["confianca"] += 0.4
            if abs(sinal["indicadores"]["momentum"]) > 0.6:
                sinal["confianca"] += 0.3
            if sinal["indicadores"]["volatilidade"] < 0.5:
                sinal["confianca"] += 0.3
            if sinal["indicadores"]["volume"]:
                sinal["confianca"] += 0.2

            sinal["confianca"] = min(sinal["confianca"], 1.0)
            sinal["forca"] = (
                "FORTE"
                if sinal["confianca"] >= 0.8
                else "MÉDIA" if sinal["confianca"] >= 0.6 else "FRACA"
            )
            momentum = sinal["indicadores"]["momentum"]
            sinal["direcao"] = (
                "ALTA" if momentum > 0.2 else "BAIXA" if momentum < -0.2 else "NEUTRO"
            )

            return sinal
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return {
                "direcao": "NEUTRO",
                "forca": "FRACA",
                "confianca": 0.0,
                "indicadores": {},
            }

    def _confirmar_tendencia(self, close):
        try:
            ma_curta = talib.SMA(close, timeperiod=9)
            ma_media = talib.SMA(close, timeperiod=21)
            ma_longa = talib.SMA(close, timeperiod=50)
            macd, signal, _ = talib.MACD(close)
            tendencia_mas = (
                ma_curta[-1] > ma_media[-1] > ma_longa[-1]
                or ma_curta[-1] < ma_media[-1] < ma_longa[-1]
            )
            tendencia_macd = macd[-1] > signal[-1] or macd[-1] < signal[-1]
            return tendencia_mas and tendencia_macd
        except Exception as e:
            logger.error(f"Erro ao confirmar tendência: {e}")
            return False

    def _verificar_volatilidade(self, high, low, close):
        try:
            atr = talib.ATR(high, low, close, timeperiod=14)
            return float(atr[-1]) / float(close[-1]) if atr.size else 1.0
        except Exception as e:
            logger.error(f"Erro ao verificar volatilidade: {e}")
            return 1.0

    def _calcular_momentum(self, close):
        try:
            rsi = talib.RSI(close, timeperiod=14)
            return (rsi[-1] - 50) / 50 if rsi.size else 0.0
        except Exception as e:
            logger.error(f"Erro ao calcular momentum: {e}")
            return 0.0

    def _verificar_volume(self, volume):
        try:
            return np.mean(volume[-20:]) >= 1000
        except Exception as e:
            logger.error(f"Erro ao verificar volume: {e}")
            return False
