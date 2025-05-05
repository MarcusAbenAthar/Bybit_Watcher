from plugins.gerenciadores.gerenciador_plugins import GerenciadorPlugins
from utils.logging_config import get_logger, log_rastreamento
from plugins.plugin import Plugin
import logging

import talib
import numpy as np
import pandas as pd
from utils.config import carregar_config
from utils.plugin_utils import (
    ajustar_periodos_generico,
    extrair_ohlcv,
    validar_klines,
    calcular_volatilidade_generico,
)

logger = get_logger(__name__)


class IndicadoresVolume(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin IndicadoresVolume, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.debug("IndicadoresVolume finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar IndicadoresVolume: {e}")

    """
    Plugin para cálculo de indicadores de volume.
    - Responsabilidade única: indicadores de volume.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "indicadores_volume"
    PLUGIN_CATEGORIA = "indicador"
    PLUGIN_TAGS = ["indicador", "volume", "analise"]
    PLUGIN_PRIORIDADE = 50

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "indicadores_volume": {
                "descricao": "Armazena valores dos indicadores de volume (OBV, MFI, CMF, etc.), score, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "indicador": "VARCHAR(50) NOT NULL",
                    "valor": "DECIMAL(18,8)",
                    "volume_base": "DECIMAL(18,8)",
                    "volume_quote": "DECIMAL(18,8)",
                    "direcao": "VARCHAR(10)",
                    "forca": "DECIMAL(5,2)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin IndicadoresVolume.
        """
        return ["gerenciador_banco", "obter_dados"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self.config = (
            config["indicadores"].get("volume", {}).copy()
            if "volume" in config["indicadores"]
            else {}
        )
        logger.debug(f"[{self.nome}] inicializado")

    def _validar_klines(self, klines, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de klines.

        Args:
            klines: Lista de k-lines.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(klines, list):
            logger.error(f"[{self.nome}] klines não é uma lista: {type(klines)}")
            log_rastreamento(
                componente=f"indicadores_volume/{symbol}-{timeframe}",
                acao="validacao_falha",
                detalhes="klines não é lista",
            )
            return False
        if len(klines) < 20:
            logger.warning(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}"
            )
            log_rastreamento(
                componente=f"indicadores_volume/{symbol}-{timeframe}",
                acao="validacao_falha",
                detalhes=f"klines insuficientes: {len(klines)}",
            )
            return False
        for item in klines:
            if not isinstance(item, (list, tuple)) or len(item) < 6:
                logger.error(
                    f"[{self.nome}] Item inválido em klines para {symbol} - {timeframe}: {item}"
                )
                log_rastreamento(
                    componente=f"indicadores_volume/{symbol}-{timeframe}",
                    acao="validacao_falha",
                    detalhes=f"item inválido: {item}",
                )
                return False
            for idx in [2, 3, 4, 5]:  # high, low, close, volume
                try:
                    float(item[idx])
                except (TypeError, ValueError):
                    logger.error(
                        f"[{self.nome}] Valor não numérico em klines[{idx}]: {item[idx]}"
                    )
                    log_rastreamento(
                        componente=f"indicadores_volume/{symbol}-{timeframe}",
                        acao="validacao_falha",
                        detalhes=f"valor não numérico em klines[{idx}]: {item[idx]}",
                    )
                    return False
        return True

    def _extrair_dados(self, dados: list, colunas: list) -> list:
        """
        Extrai arrays NumPy das colunas OHLCV com base nos índices informados.

        Args:
            dados: Lista de k-lines.
            colunas: Lista de índices para extração (ex.: [2, 3, 4, 5] para high, low, close, volume).

        Returns:
            list: Lista de arrays NumPy para cada coluna.
        """
        try:
            dados_completos = list(zip(*dados))
            return [np.array(dados_completos[i], dtype=np.float64) for i in colunas]
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair dados: {e}")
            return [np.array([]) for _ in colunas]

    def _ajustar_periodo(self, timeframe: str, volatilidade: float) -> int:
        """
        Ajusta o período dos indicadores com base no timeframe e volatilidade.

        Args:
            timeframe (str): Timeframe (ex.: '1m', '1d').
            volatilidade (float): Volatilidade calculada.

        Returns:
            int: Período ajustado.
        """
        base = self.config["periodo_base"]
        if timeframe == "1m":
            base = max(self.config["periodo_minimo"], base // 2)
        elif timeframe == "1d":
            base = min(self.config["periodo_maximo"], base * 2)

        base += int(volatilidade * 10)
        return max(
            self.config["periodo_minimo"], min(base, self.config["periodo_maximo"])
        )

    def calcular_obv(self, close: np.ndarray, volume: np.ndarray):
        """
        Calcula o On-Balance Volume (OBV).

        Args:
            close: Array de preços de fechamento.
            volume: Array de volumes.

        Returns:
            np.ndarray: Valores do OBV ou array vazio em caso de erro.
        """
        try:
            return talib.OBV(close, volume)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular OBV: {e}")
            return np.array([])

    def calcular_mfi(self, high, low, close, volume, periodo):
        """
        Calcula o Money Flow Index (MFI).

        Args:
            high, low, close, volume: Arrays de preços e volume.
            periodo: Período para cálculo.

        Returns:
            np.ndarray: Valores do MFI ou array vazio em caso de erro.
        """
        try:
            return talib.MFI(high, low, close, volume, timeperiod=periodo)
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular MFI: {e}")
            return np.array([])

    def calcular_cmf(self, high, low, close, volume, periodo):
        """
        Calcula o Chaikin Money Flow (CMF).

        Args:
            high, low, close, volume: Arrays de preços e volume.
            periodo: Período para cálculo.

        Returns:
            np.ndarray: Valores do CMF ou array vazio em caso de erro.
        """
        try:
            money_flow_volume = (
                (2 * close - high - low) / (high - low + 1e-6)
            ) * volume
            mfv_sum = pd.Series(money_flow_volume).rolling(window=periodo).sum()
            vol_sum = pd.Series(volume).rolling(window=periodo).sum()
            cmf = (mfv_sum / (vol_sum + 1e-6)).fillna(0.0)
            return cmf.to_numpy()
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular CMF: {e}")
            return np.array([])

    def calcular_volatilidade(self, close, periodo=14) -> float:
        """
        Calcula a volatilidade com base no desvio padrão relativo.

        Args:
            close: Array de preços de fechamento.
            periodo: Período para cálculo.

        Returns:
            float: Valor da volatilidade ou 0.0 em caso de erro.
        """
        try:
            std = talib.STDDEV(close, timeperiod=periodo)
            return (
                float(std[-1]) / float(close[-1])
                if std.size > 0 and close[-1] != 0
                else 0.0
            )
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular volatilidade: {e}")
            return 0.0

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a análise de volume.

        Args:
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados, deve incluir dados_completos

        Returns:
            bool: True se executado com sucesso
        """
        from utils.logging_config import log_rastreamento

        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"indicadores_volume/{symbol}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        resultado_padrao = {"obv": None, "cmf": None, "mfi": None}
        try:
            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros ausentes")
                if isinstance(dados_completos, dict):
                    dados_completos["volume"] = resultado_padrao
                return True
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                dados_completos["volume"] = resultado_padrao
                return True
            klines = dados_completos.get("crus", [])
            if not validar_klines(klines, min_len=20):
                dados_completos["volume"] = resultado_padrao
                return True
            extr = extrair_ohlcv(klines, [2, 3, 4, 5])
            high, low, close, volume = extr[2], extr[3], extr[4], extr[5]
            log_rastreamento(
                componente=f"indicadores_volume/{symbol}-{timeframe}",
                acao="dados_extraidos",
                detalhes=f"len_volume={len(volume)}, volume_exemplo={volume[-5:].tolist() if len(volume) >= 5 else volume.tolist()}",
            )
            if not all([high.size, low.size, close.size, volume.size]):
                logger.warning(
                    f"[{self.nome}] Dados extraídos vazios para {symbol} - {timeframe}"
                )
                dados_completos["volume"] = resultado_padrao
                return True
            volatilidade = calcular_volatilidade_generico(
                close, periodo=self.config.get("periodo_base", 14)
            )
            periodo = ajustar_periodos_generico(
                {"periodo": self.config.get("periodo_base", 14)},
                timeframe,
                volatilidade,
            )["periodo"]
            obv = talib.OBV(close, volume)
            # CMF
            try:
                money_flow_volume = (
                    (2 * close - high - low) / (high - low + 1e-6)
                ) * volume
                mfv_sum = pd.Series(money_flow_volume).rolling(window=periodo).sum()
                vol_sum = pd.Series(volume).rolling(window=periodo).sum()
                cmf = (mfv_sum / (vol_sum + 1e-6)).fillna(0.0).to_numpy()
            except Exception as e:
                logger.error(f"[{self.nome}] Erro ao calcular CMF: {e}")
                cmf = np.array([])
            mfi = talib.MFI(high, low, close, volume, timeperiod=periodo)
            log_rastreamento(
                componente=f"indicadores_volume/{symbol}-{timeframe}",
                acao="indicadores_calculados",
                detalhes=(
                    f"obv={obv[-1] if obv.size > 0 else None}, "
                    f"cmf={cmf[-1] if cmf.size > 0 else None}, "
                    f"mfi={mfi[-1] if mfi.size > 0 else None}"
                ),
            )
            resultado = {
                "obv": float(obv[-1]) if obv.size > 0 else None,
                "cmf": float(cmf[-1]) if cmf.size > 0 else None,
                "mfi": float(mfi[-1]) if mfi.size > 0 else None,
            }
            dados_completos["volume"] = resultado
            logger.debug(
                f"[{self.nome}] Indicadores de volume gerados para {symbol} - {timeframe}: {resultado}"
            )
            log_rastreamento(
                componente=f"indicadores_volume/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"indicadores_volume={resultado}",
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro geral na execução: {e}", exc_info=True)
            if isinstance(dados_completos, dict):
                dados_completos["volume"] = resultado_padrao
            return False
