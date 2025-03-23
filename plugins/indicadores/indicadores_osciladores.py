# indicadores_osciladores.py
# Plugin para cálculo de indicadores osciladores (RSI, Estocástico, MFI)

from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresOsciladores(Plugin):
    PLUGIN_NAME = "indicadores_osciladores"
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

    def calcular_rsi(self, dados, symbol, timeframe, periodo=14):
        try:
            if timeframe == "1m":
                periodo = max(7, periodo // 2)
            elif timeframe == "1d":
                periodo = min(28, periodo * 2)
            volatilidade = self.calcular_volatilidade(dados)
            periodo = max(7, min(28, periodo + int(volatilidade * 10)))

            dados_extraidos = self._extrair_dados(dados, [4])
            close = dados_extraidos[4]
            if len(close) < periodo:
                return np.array([])

            rsi = talib.RSI(close, timeperiod=periodo)
            logger.debug(f"RSI calculado para {symbol} - {timeframe}")
            return rsi
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {e}")
            return np.array([])

    def calcular_estocastico(
        self, dados, timeframe, fastk_period=5, slowk_period=3, slowd_period=3
    ):
        try:
            if timeframe == "1m":
                fastk_period = max(3, fastk_period // 2)
                slowk_period = max(2, slowk_period // 2)
                slowd_period = max(2, slowd_period // 2)
            elif timeframe == "1d":
                fastk_period = min(10, fastk_period * 2)
                slowk_period = min(6, slowk_period * 2)
                slowd_period = min(6, slowd_period * 2)
            volatilidade = self.calcular_volatilidade(dados)
            ajuste = int(volatilidade * 3)
            fastk_period = max(3, min(10, fastk_period + ajuste))
            slowk_period = max(2, min(6, slowk_period + ajuste))
            slowd_period = max(2, min(6, slowd_period + ajuste))

            dados_extraidos = self._extrair_dados(dados, [2, 3, 4])
            high, low, close = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
            )
            if len(high) < max(fastk_period, slowk_period, slowd_period):
                return np.array([]), np.array([])

            slowk, slowd = talib.STOCH(
                high,
                low,
                close,
                fastk_period=fastk_period,
                slowk_period=slowk_period,
                slowk_matype=0,
                slowd_period=slowd_period,
                slowd_matype=0,
            )
            return slowk, slowd
        except Exception as e:
            logger.error(f"Erro ao calcular Estocástico: {e}")
            return np.array([]), np.array([])

    def calcular_mfi(self, dados, periodo=14):
        try:
            dados_extraidos = self._extrair_dados(dados, [2, 3, 4, 5])
            high, low, close, volume = (
                dados_extraidos[2],
                dados_extraidos[3],
                dados_extraidos[4],
                dados_extraidos[5],
            )
            if len(high) < periodo:
                return np.array([])

            mfi = talib.MFI(high, low, close, volume, timeperiod=periodo)
            return mfi
        except Exception as e:
            logger.error(f"Erro ao calcular MFI: {e}")
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

            if indicador == "rsi":
                rsi = self.calcular_rsi(dados, symbol, timeframe)
                if rsi.size:
                    total_indicadores += 1
                    if tipo == "sobrecompra" and rsi[-1] > 70:
                        confirmacoes_venda += 1
                    elif tipo == "sobrevenda" and rsi[-1] < 30:
                        confirmacoes_compra += 1

            elif indicador == "estocastico":
                slowk, slowd = self.calcular_estocastico(dados, timeframe)
                if slowk.size and slowd.size:
                    total_indicadores += 1
                    if tipo == "sobrecompra" and slowk[-1] > 80 and slowd[-1] > 80:
                        confirmacoes_venda += 1
                    elif tipo == "sobrevenda" and slowk[-1] < 20 and slowd[-1] < 20:
                        confirmacoes_compra += 1

            elif indicador == "mfi":
                mfi = self.calcular_mfi(dados)
                if mfi.size:
                    total_indicadores += 1
                    if tipo == "sobrecompra" and mfi[-1] > 80:
                        confirmacoes_venda += 1
                    elif tipo == "sobrevenda" and mfi[-1] < 20:
                        confirmacoes_compra += 1

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
            "rsi": None,
            "estocastico": {"lento": None, "rapido": None},
            "mfi": None,
            "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
        }
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            if not all([dados, symbol, timeframe]):
                logger.error(f"Parâmetros necessários não fornecidos")
                if isinstance(dados, dict):
                    dados["osciladores"] = resultado_padrao
                return True

            if not isinstance(dados, list) or len(dados) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados["osciladores"] = resultado_padrao
                return True

            rsi = self.calcular_rsi(dados, symbol, timeframe)
            slowk, slowd = self.calcular_estocastico(dados, timeframe)
            mfi = self.calcular_mfi(dados)

            resultado = {
                "rsi": rsi[-1] if rsi.size > 0 else None,
                "estocastico": {
                    "lento": slowk[-1] if slowk.size > 0 else None,
                    "rapido": slowd[-1] if slowd.size > 0 else None,
                },
                "mfi": mfi[-1] if mfi.size > 0 else None,
                "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
            }

            if isinstance(dados, dict):
                dados["osciladores"] = resultado

            if self.banco_dados and hasattr(self.banco_dados, "conn"):
                try:
                    timestamp = int(dados[-1][0] / 1000)
                    cursor = self.banco_dados.conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO indicadores_osciladores (
                            symbol, timeframe, timestamp, rsi, estocastico_lento,
                            estocastico_rapido, mfi
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) 
                        DO UPDATE SET
                            rsi = EXCLUDED.rsi,
                            estocastico_lento = EXCLUDED.estocastico_lento,
                            estocastico_rapido = EXCLUDED.estocastico_rapido,
                            mfi = EXCLUDED.mfi
                        """,
                        (
                            symbol,
                            timeframe,
                            timestamp,
                            resultado["rsi"],
                            resultado["estocastico"]["lento"],
                            resultado["estocastico"]["rapido"],
                            resultado["mfi"],
                        ),
                    )
                    self.banco_dados.conn.commit()
                    logger.debug(f"Dados salvos no banco para {symbol} - {timeframe}")
                except Exception as e:
                    logger.error(f"Erro ao salvar no banco: {e}")

            return True
        except Exception as e:
            logger.error(f"Erro ao executar indicadores osciladores: {e}")
            if isinstance(dados, dict):
                dados["osciladores"] = resultado_padrao
            return True
