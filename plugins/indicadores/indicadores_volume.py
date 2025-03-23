# indicadores_volume.py
# Plugin para calcular indicadores de volume

from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin

logger = get_logger(__name__)


class IndicadoresVolume(Plugin):
    PLUGIN_NAME = "indicadores_volume"
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

    def calcular_obv(self, dados):
        try:
            dados_extraidos = self._extrair_dados(dados, [4, 5])
            close, volume = dados_extraidos[4], dados_extraidos[5]
            if len(close) < 2:
                return np.array([])
            return talib.OBV(close, volume)
        except Exception as e:
            logger.error(f"Erro ao calcular OBV: {e}")
            return np.array([])

    def calcular_cmf(self, dados, periodo=20):
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
            return talib.CMF(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"Erro ao calcular CMF: {e}")
            return np.array([])

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
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
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

    def verificar_divergencia(self, dados, indicador, tipo="altista"):
        try:
            if len(dados) < 3 or len(indicador) < 3:
                return False
            fechamentos = self._extrair_dados(dados, [4])[4]
            if tipo == "altista":
                return (fechamentos[-1] < fechamentos[-3]) and (
                    indicador[-1] > indicador[-3]
                )
            elif tipo == "baixista":
                return (fechamentos[-1] > fechamentos[-3]) and (
                    indicador[-1] < indicador[-3]
                )
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar divergência: {e}")
            return False

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

            if indicador == "obv":
                obv = self.calcular_obv(dados)
                if obv.size:
                    total_indicadores += 1
                    if tipo == "divergencia_altista" and self.verificar_divergencia(
                        dados, obv, "altista"
                    ):
                        confirmacoes_compra += 1
                    elif tipo == "divergencia_baixista" and self.verificar_divergencia(
                        dados, obv, "baixista"
                    ):
                        confirmacoes_venda += 1

            elif indicador == "cmf":
                cmf = self.calcular_cmf(dados)
                if cmf.size and len(cmf) > 1:
                    total_indicadores += 1
                    if tipo == "cruzamento_acima" and cmf[-1] > 0 and cmf[-2] < 0:
                        confirmacoes_compra += 1
                    elif tipo == "cruzamento_abaixo" and cmf[-1] < 0 and cmf[-2] > 0:
                        confirmacoes_venda += 1

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
            "obv": None,
            "cmf": None,
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
                    dados["volume"] = resultado_padrao
                return True

            if not isinstance(dados, list) or len(dados) < 20:
                logger.warning(f"Dados insuficientes para {symbol} - {timeframe}")
                if isinstance(dados, dict):
                    dados["volume"] = resultado_padrao
                return True

            obv = self.calcular_obv(dados)
            cmf = self.calcular_cmf(dados)
            mfi = self.calcular_mfi(dados)

            resultado = {
                "obv": obv[-1] if obv.size > 0 else None,
                "cmf": cmf[-1] if cmf.size > 0 else None,
                "mfi": mfi[-1] if mfi.size > 0 else None,
                "sinais": {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0},
            }

            if isinstance(dados, dict):
                dados["volume"] = resultado

            if self.banco_dados and hasattr(self.banco_dados, "conn"):
                try:
                    timestamp = int(dados[-1][0] / 1000)
                    cursor = self.banco_dados.conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO indicadores_volume (
                            symbol, timeframe, timestamp, obv, cmf, mfi
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) 
                        DO UPDATE SET
                            obv = EXCLUDED.obv,
                            cmf = EXCLUDED.cmf,
                            mfi = EXCLUDED.mfi
                        """,
                        (
                            symbol,
                            timeframe,
                            timestamp,
                            resultado["obv"],
                            resultado["cmf"],
                            resultado["mfi"],
                        ),
                    )
                    self.banco_dados.conn.commit()
                    logger.debug(f"Dados salvos no banco para {symbol} - {timeframe}")
                except Exception as e:
                    logger.error(f"Erro ao salvar no banco: {e}")

            return True
        except Exception as e:
            logger.error(f"Erro ao executar indicadores volume: {e}")
            if isinstance(dados, dict):
                dados["volume"] = resultado_padrao
            return True
