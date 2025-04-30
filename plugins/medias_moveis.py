"""
Plugin para cálculo de sinais baseados em médias móveis.
"""

from utils.logging_config import get_logger
import numpy as np
import talib
from plugins.plugin import Plugin

logger = get_logger(__name__)


class MediasMoveis(Plugin):
    """
    Plugin de análise de Médias Móveis (MA).
    - Responsabilidade única: análise de médias móveis.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "medias_moveis"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "medias_moveis", "ma"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin MediasMoveis.
        """
        return []

    PLUGIN_NAME = "medias_moveis"
    PLUGIN_CATEGORIA = "plugin"
    # Adicionada a tag 'analise' para garantir execução no pipeline de análise do bot.
    PLUGIN_TAGS = ["tendencia", "indicador", "mm", "analise"]
    PLUGIN_PRIORIDADE = 40

    def __init__(self, **kwargs):
        """
        Inicializa o plugin de médias móveis.
        """
        super().__init__(**kwargs)
        self._periodo_curto = 20  # Padrão para MA curta
        self._periodo_longo = 50  # Padrão para MA longa

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações (ex.: períodos das médias).

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            self._periodo_curto = config.get("medias_moveis", {}).get(
                "periodo_curto", self._periodo_curto
            )
            self._periodo_longo = config.get("medias_moveis", {}).get(
                "periodo_longo", self._periodo_longo
            )

            if not (
                isinstance(self._periodo_curto, int)
                and isinstance(self._periodo_longo, int)
                and self._periodo_curto > 0
                and self._periodo_longo > self._periodo_curto
            ):
                logger.error(
                    f"[{self.nome}] Períodos inválidos: curto={self._periodo_curto}, longo={self._periodo_longo}"
                )
                return False

            logger.info(
                f"[{self.nome}] inicializado com períodos curto={self._periodo_curto}, longo={self._periodo_longo}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def _validar_klines(self, klines: list, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de klines.

        Args:
            klines: Lista de k-lines.
            symbol: Símbolo do par.
            timeframe: Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(klines, list):
            logger.error(f"[{self.nome}] klines não é uma lista: {type(klines)}")
            return False

        if len(klines) < self._periodo_longo:
            logger.error(
                f"[{self.nome}] Dados insuficientes para {symbol} - {timeframe}: {len(klines)} klines, "
                f"requer {self._periodo_longo}"
            )
            return False

        for kline in klines:
            if not isinstance(kline, (list, tuple)) or len(kline) < 6:
                logger.error(
                    f"[{self.nome}] K-line malformada para {symbol} - {timeframe}: {kline}"
                )
                return False
            try:
                # Verificar se close e volume são numéricos
                float(kline[4])  # close
                float(kline[5])  # volume
            except (TypeError, ValueError):
                logger.error(
                    f"[{self.nome}] Valor não numérico em k-line para {symbol} - {timeframe}: {kline}"
                )
                return False

        return True

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo de sinais de médias móveis e armazena resultados.

        Args:
            dados_completos (dict): Dados crus e processados.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")

        logger.debug(f"[{self.nome}] Iniciando para {symbol} - {timeframe}")

        resultado_padrao = {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.0,
            "indicadores": {"ma_curta": None, "ma_longa": None},
        }

        if not isinstance(dados_completos, dict) or not all([symbol, timeframe]):
            logger.error(f"[{self.nome}] Parâmetros inválidos recebidos")
            if isinstance(dados_completos, dict):
                dados_completos["medias_moveis"] = resultado_padrao
            return True

        dados_crus = dados_completos.get("crus", [])
        if not self._validar_klines(dados_crus, symbol, timeframe):
            dados_completos["medias_moveis"] = resultado_padrao
            return True

        try:
            sinal = self.gerar_sinal(dados_crus)
            dados_completos["medias_moveis"] = sinal
            logger.info(f"[{self.nome}] Concluído para {symbol} - {timeframe}")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao processar: {e}", exc_info=True)
            dados_completos["medias_moveis"] = resultado_padrao
            return True

    def _extrair_dados(self, crus: list, indices: list) -> dict:
        """
        Extrai dados especificados das k-lines.

        Args:
            crus: Lista de k-lines.
            indices: Lista de índices a extrair (ex.: [4] para close, [5] para volume).

        Returns:
            dict: Dicionário com arrays para cada índice (ex.: {4: closes, 5: volumes}).
        """
        try:
            result = {}
            for idx in indices:
                result[idx] = np.array([float(c[idx]) for c in crus], dtype=np.float64)
            return result
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair dados: {e}", exc_info=True)
            return {idx: np.array([]) for idx in indices}

    def gerar_sinal(self, crus: list) -> dict:
        """
        Gera sinal baseado em médias móveis.

        Args:
            crus: Lista de k-lines.

        Returns:
            dict: Sinal com direção, força, confiança e valores das médias.
        """
        try:
            dados = self._extrair_dados(crus, [4, 5])  # close e volume
            closes = dados[4]
            volumes = dados[5]

            if len(closes) < self._periodo_longo or len(volumes) < self._periodo_longo:
                logger.warning(
                    f"[{self.nome}] Menos de {self._periodo_longo} candles disponíveis"
                )
                return self._resultado_padrao()

            ma_curta = talib.SMA(closes, timeperiod=self._periodo_curto)
            ma_longa = talib.SMA(closes, timeperiod=self._periodo_longo)

            if ma_curta[-1] is None or ma_longa[-1] is None:
                logger.warning(f"[{self.nome}] Médias móveis inválidas")
                return self._resultado_padrao()

            # Calcular direção
            valid_range = range(len(ma_curta) - 5, len(ma_curta))
            tendencia_alta = sum(
                ma_curta[i] > ma_longa[i]
                for i in valid_range
                if ma_curta[i] and ma_longa[i]
            )
            tendencia_baixa = sum(
                ma_curta[i] < ma_longa[i]
                for i in valid_range
                if ma_curta[i] and ma_longa[i]
            )
            direcao = (
                "ALTA"
                if tendencia_alta > tendencia_baixa
                else "BAIXA" if tendencia_baixa > tendencia_alta else "LATERAL"
            )

            # Calcular distância e confiança
            distancia = abs(ma_curta[-1] - ma_longa[-1]) / ma_longa[-1]
            vol_rel = (
                volumes[-1] / np.mean(volumes[-10:])
                if np.mean(volumes[-10:]) > 0
                else 1.0
            )
            atr = talib.ATR(
                np.array([float(c[2]) for c in crus], dtype=np.float64),  # high
                np.array([float(c[3]) for c in crus], dtype=np.float64),  # low
                closes,
                timeperiod=14,
            )
            volatilidade = (
                atr[-1] / closes[-1] if atr[-1] is not None and closes[-1] > 0 else 0.0
            )

            base_conf = max(tendencia_alta, tendencia_baixa) / 5
            confianca = base_conf * (0.5 + 0.3 * vol_rel + 0.2 * volatilidade)
            confianca = round(min(max(confianca, 0.0), 1.0), 2)

            # Calcular força
            forca = (
                "FORTE"
                if confianca >= 0.7
                else "MÉDIA" if confianca >= 0.3 else "FRACA"
            )

            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "indicadores": {
                    "ma_curta": round(ma_curta[-1], 4),
                    "ma_longa": round(ma_longa[-1], 4),
                },
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao gerar sinal: {e}", exc_info=True)
            return self._resultado_padrao()

    def _resultado_padrao(self) -> dict:
        """
        Retorna o resultado padrão para casos de erro.

        Returns:
            dict: Resultado com valores padrão.
        """
        return {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.0,
            "indicadores": {"ma_curta": None, "ma_longa": None},
        }
