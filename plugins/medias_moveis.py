"""
Plugin de médias móveis.
Responsabilidade única: cálculo e análise de médias móveis.
Não deve registrar, inicializar ou finalizar automaticamente.
Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
"""

from utils.logging_config import get_logger, log_banco, log_rastreamento
import numpy as np
import talib
from plugins.plugin import Plugin
from datetime import datetime
from utils.config import carregar_config
from utils.plugin_utils import validar_klines

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

    def __init__(self, **kwargs):
        """
        Inicializa o plugin de médias móveis.
        """
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("medias_moveis", {}).copy()
            if "plugins" in config and "medias_moveis" in config["plugins"]
            else {}
        )
        self._periodo_curto = self._config.get(
            "periodo_curto", 20
        )  # Padrão para MA curta
        self._periodo_longo = self._config.get(
            "periodo_longo", 50
        )  # Padrão para MA longa

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
        from utils.logging_config import log_rastreamento

        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos")
        log_rastreamento(
            componente=f"medias_moveis/{symbol}-{timeframe}",
            acao="entrada",
            detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
        )
        resultado_padrao = {"medias_moveis": {}}
        try:
            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                return resultado_padrao
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                return resultado_padrao
            candles = dados_completos.get("crus", [])
            if not self._validar_klines(candles, symbol, timeframe):
                return resultado_padrao
            medias = self.gerar_sinal(candles)
            logger.debug(
                f"[{self.nome}] Médias móveis para {symbol}-{timeframe}: {medias}"
            )
            log_rastreamento(
                componente=f"medias_moveis/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"medias_moveis={medias}",
            )
            if isinstance(dados_completos, dict):
                dados_completos["medias_moveis"] = medias
            return {"medias_moveis": medias}
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return resultado_padrao

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
        Gera sinal baseado em médias móveis, com decisão mais flexível e logs detalhados.
        Se pelo menos 3 dos últimos 5 candles apontarem para ALTA ou BAIXA, já considera a direção.
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
            # Log detalhado das médias e closes
            logger.info(
                f"[{self.nome}] Últimos closes: {closes[-5:].tolist() if hasattr(closes, 'tolist') else closes[-5:]}"
            )
            logger.info(
                f"[{self.nome}] Últimas ma_curta: {ma_curta[-5:].tolist() if hasattr(ma_curta, 'tolist') else ma_curta[-5:]}"
            )
            logger.info(
                f"[{self.nome}] Últimas ma_longa: {ma_longa[-5:].tolist() if hasattr(ma_longa, 'tolist') else ma_longa[-5:]}"
            )
            # Decisão mais flexível
            valid_range = range(len(ma_curta) - 5, len(ma_curta))
            alta = sum(ma_curta[i] > ma_longa[i] for i in valid_range)
            baixa = sum(ma_curta[i] < ma_longa[i] for i in valid_range)
            if alta >= 3:
                direcao = "ALTA"
            elif baixa >= 3:
                direcao = "BAIXA"
            else:
                direcao = "LATERAL"
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
            base_conf = max(alta, baixa) / 5
            confianca = base_conf * (0.5 + 0.3 * vol_rel + 0.2 * volatilidade)
            confianca = round(min(max(confianca, 0.0), 1.0), 2)
            forca = (
                "FORTE"
                if confianca >= 0.7
                else "MÉDIA" if confianca >= 0.3 else "FRACA"
            )
            logger.info(
                f"[{self.nome}] Decisão: DIREÇÃO={direcao}, FORÇA={forca}, CONFIANÇA={confianca}, VOL_REL={vol_rel}, VOLATILIDADE={volatilidade}"
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

    @property
    def plugin_tabelas(self) -> dict:
        """
        Define as tabelas do plugin conforme padrão institucional (regras de ouro).
        """
        return {
            "medias_moveis": {
                "descricao": "Armazena médias móveis calculadas, faixas, score, contexto e demais métricas relevantes.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "ma_curta": "DECIMAL(18,8)",
                    "ma_longa": "DECIMAL(18,8)",
                    "faixa_ma_curta_min": "DECIMAL(18,8)",
                    "faixa_ma_curta_max": "DECIMAL(18,8)",
                    "faixa_ma_longa_min": "DECIMAL(18,8)",
                    "faixa_ma_longa_max": "DECIMAL(18,8)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
