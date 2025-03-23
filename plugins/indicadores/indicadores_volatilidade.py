# indicadores_volatilidade.py
# Plugin para calcular indicadores de volatilidade e gerar sinais de compra e venda

from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresVolatilidade(Plugin):
    PLUGIN_NAME = "indicadores_volatilidade"
    PLUGIN_TYPE = "indicador"

    def __init__(self, gerente: GerentePlugin, config=None):
        super().__init__()
        self.nome = self.PLUGIN_NAME
        self.config = config or {}
        self.gerente = gerente
        self.banco_dados = self.gerente.obter_plugin("banco_dados")

    def _extrair_dados(self, dados, indices):
        try:
            valores = {idx: [] for idx in indices}
            for candle in dados:
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
                logger.warning("Dados insuficientes ou inválidos")
                return {idx: np.array([]) for idx in indices}
            return {idx: np.array(valores[idx], dtype=np.float64) for idx in indices}
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return {idx: np.array([]) for idx in indices}

    def calcular_bandas_de_bollinger(self, dados, periodo=20, desvio_padrao=2):
        try:
            dados_extraidos = self._extrair_dados(dados, [4])
            close = dados_extraidos[4]
            if len(close) < periodo:
                logger.warning(
                    f"Dados insuficientes para Bandas de Bollinger: {len(close)}/{periodo}"
                )
                return np.array([]), np.array([]), np.array([])

            banda_media = talib.SMA(close, timeperiod=periodo)
            std_dev = talib.STDDEV(close, timeperiod=periodo)
            banda_superior = banda_media + std_dev * desvio_padrao
            banda_inferior = banda_media - std_dev * desvio_padrao
            return banda_superior, banda_media, banda_inferior
        except Exception as e:
            logger.error(f"Erro ao calcular Bandas de Bollinger: {e}")
            return np.array([]), np.array([]), np.array([])

    def calcular_atr(self, dados, periodo=14):
        try:
            dados_extraidos = self._extrair_dados(dados, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(high) < periodo:
                logger.warning(f"Dados insuficientes para ATR: {len(high)}/{periodo}")
                return np.array([])

            atr = talib.ATR(high, low, close, timeperiod=periodo)
            return atr
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {e}")
            return np.array([])

    def calcular_volatilidade(self, dados, periodo=14):
        try:
            if len(dados) < periodo:
                return 0.0
            dados_extraidos = self._extrair_dados(dados, [4])
            close = dados_extraidos[4]
            std = talib.STDDEV(close, timeperiod=periodo)
            return (
                min(max(float(std[-1]) / float(close[-1]), 0.0), 1.0)
                if len(std) > 0
                else 0.0
            )
        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {e}")
            return 0.0

    def gerar_sinal(self, dados, indicador, tipo, symbol, timeframe, config):
        resultado_padrao = {
            "direcao": "NEUTRO",
            "forca": "FRACA",
            "confianca": 0.0,
            "stop_loss": None,
            "take_profit": None,
        }
        try:
            if len(dados) < 20:
                return resultado_padrao

            ultimo_preco = float(dados[-1][4])
            volatilidade = self.calcular_volatilidade(dados)
            total_indicadores = 0
            confirmacoes_compra = 0
            confirmacoes_venda = 0

            if indicador == "bandas_de_bollinger":
                upper, middle, lower = self.calcular_bandas_de_bollinger(dados)
                if upper.size and middle.size and lower.size:
                    total_indicadores += 1
                    if tipo == "rompimento_superior" and ultimo_preco > upper[-1]:
                        confirmacoes_compra += 1
                    elif tipo == "rompimento_inferior" and ultimo_preco < lower[-1]:
                        confirmacoes_venda += 1

            elif indicador == "atr":
                atr = self.calcular_atr(dados)
                if atr.size and len(dados) > 1:
                    total_indicadores += 1
                    penultimo_preco = float(dados[-2][4])
                    if (
                        tipo == "rompimento_alta"
                        and ultimo_preco > penultimo_preco + atr[-1]
                    ):
                        confirmacoes_compra += 1
                    elif (
                        tipo == "rompimento_baixa"
                        and ultimo_preco < penultimo_preco - atr[-1]
                    ):
                        confirmacoes_venda += 1

            if total_indicadores == 0:
                return resultado_padrao

            confianca_compra = confirmacoes_compra / total_indicadores
            confianca_venda = confirmacoes_venda / total_indicadores
            forca = "FRACA" if total_indicadores < 2 else "MÉDIA"
            ajuste_tp_sl = volatilidade * ultimo_preco

            if confianca_compra >= 0.8:
                return {
                    "direcao": "ALTA",
                    "forca": forca,
                    "confianca": confianca_compra * 100,
                    "stop_loss": ultimo_preco - ajuste_tp_sl * 1.5,
                    "take_profit": ultimo_preco + ajuste_tp_sl * 2,
                }
            elif confianca_venda >= 0.8:
                return {
                    "direcao": "BAIXA",
                    "forca": forca,
                    "confianca": confianca_venda * 100,
                    "stop_loss": ultimo_preco + ajuste_tp_sl * 1.5,
                    "take_profit": ultimo_preco - ajuste_tp_sl * 2,
                }
            return resultado_padrao
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {e}")
            return resultado_padrao

    def executar(self, *args, **kwargs) -> bool:
        resultado_padrao = {
            "bandas_bollinger": {"superior": None, "media": None, "inferior": None},
            "atr": None,
            "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados["volatilidade"] = resultado_padrao
                return True

            if not isinstance(dados, list) or len(dados) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados["volatilidade"] = resultado_padrao
                return True

            upper, middle, lower = self.calcular_bandas_de_bollinger(dados)
            atr = self.calcular_atr(dados)

            resultado = {
                "bandas_bollinger": {
                    "superior": upper[-1] if upper.size > 0 else None,
                    "media": middle[-1] if middle.size > 0 else None,
                    "inferior": lower[-1] if lower.size > 0 else None,
                },
                "atr": atr[-1] if atr.size > 0 else None,
                "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
            }

            if isinstance(dados, dict):
                dados["volatilidade"] = resultado

            if self.banco_dados and hasattr(self.banco_dados, "conn"):
                try:
                    timestamp = int(dados[-1][0] / 1000)
                    cursor = self.banco_dados.conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO indicadores_volatilidade (
                            symbol, timeframe, timestamp, bandas_superior, bandas_media,
                            bandas_inferior, atr
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) 
                        DO UPDATE SET
                            bandas_superior = EXCLUDED.bandas_superior,
                            bandas_media = EXCLUDED.bandas_media,
                            bandas_inferior = EXCLUDED.bandas_inferior,
                            atr = EXCLUDED.atr
                        """,
                        (
                            symbol,
                            timeframe,
                            timestamp,
                            resultado["bandas_bollinger"]["superior"],
                            resultado["bandas_bollinger"]["media"],
                            resultado["bandas_bollinger"]["inferior"],
                            resultado["atr"],
                        ),
                    )
                    self.banco_dados.conn.commit()
                    logger.debug(f"Dados salvos no banco para {symbol} - {timeframe}")
                except Exception as e:
                    logger.error(f"Erro ao salvar no banco: {e}")

            return True
        except Exception as e:
            logger.error(f"Erro ao executar indicadores volatilidade: {e}")
            if isinstance(dados, dict):
                dados["volatilidade"] = resultado_padrao
            return True
