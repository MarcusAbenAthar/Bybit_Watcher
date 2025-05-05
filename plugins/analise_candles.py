"""Plugin para detecção de padrões de candle com TA-Lib."""

import os
import json
import numpy as np
import talib
from typing import Dict, Any, List
import datetime

from utils.logging_config import get_logger
from plugins.plugin import Plugin
from utils.config import carregar_config
from utils.plugin_utils import validar_klines

logger = get_logger(__name__)


class AnaliseCandles(Plugin):
    """
    Plugin de análise de padrões de candles (ex: martelo, engolfo, etc).
    - Responsabilidade única: análise de padrões de candles.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "analise_candles"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["analise", "candles", "padroes"]
    PLUGIN_PRIORIDADE = 100

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        tabelas = {
            "padroes_candles": {
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "padrao": "VARCHAR(50) NOT NULL",
                    "direcao": "VARCHAR(10) NOT NULL",
                    "forca": "DECIMAL(5,2)",
                    "confianca": "DECIMAL(5,2)",
                    "preco_entrada": "DECIMAL(18,8)",
                    "stop_loss": "DECIMAL(18,8)",
                    "take_profit": "DECIMAL(18,8)",
                    "volume": "DECIMAL(18,8)",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
            }
        }
        return tabelas

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin AnaliseCandles.
        """
        return ["gerenciador_banco"]

    def __init__(self, **kwargs):
        """
        Inicializa o plugin AnaliseCandles.

        Args:
            **kwargs: Outras dependências
        """
        super().__init__(**kwargs)
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("analise_candles", {}).copy()
            if "plugins" in config and "analise_candles" in config["plugins"]
            else {}
        )
        self._gerente = kwargs.get("gerente")
        self._gerenciador_banco = kwargs.get("gerenciador_banco")
        self._padroes_talib = self._carregar_padroes()
        self._funcoes_talib = self._mapear_funcoes_talib()

    def _mapear_funcoes_talib(self) -> Dict[str, callable]:
        """
        Mapeia os nomes dos padrões para as funções do TA-Lib.
        """
        funcoes = {}
        for padrao in self._padroes_talib:
            nome_funcao = f"CDL{padrao.upper()}"
            if hasattr(talib, nome_funcao):
                funcoes[padrao] = getattr(talib, nome_funcao)
        return funcoes

    def _carregar_padroes(self) -> set:
        """
        Carrega os padrões TA-Lib do arquivo JSON.

        Returns:
            set: Conjunto de nomes de padrões TA-Lib.
        """
        caminho = os.path.join("utils", "padroes_talib.json")
        try:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo {caminho} não encontrado.")

            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)

            padroes = set(data.get("padroes_talib", []))
            if not padroes:
                logger.error(f"[{self.nome}] Nenhum padrão TA-Lib carregado do JSON.")
                raise ValueError("Lista de padrões TA-Lib vazia.")
            return padroes

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao carregar padrões TA-Lib: {e}")
            return set()

    def _extrair_ohlcv(self, candles: list) -> dict:
        """Extrai arrays OHLCV dos candles."""
        try:
            dados = list(zip(*candles))
            return {
                "timestamp": np.array(dados[0], dtype=np.float64),
                "open": np.array(dados[1], dtype=np.float64),
                "high": np.array(dados[2], dtype=np.float64),
                "low": np.array(dados[3], dtype=np.float64),
                "close": np.array(dados[4], dtype=np.float64),
                "volume": np.array(dados[5], dtype=np.float64),
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair OHLCV: {e}")
            return {
                "timestamp": np.array([]),
                "open": np.array([]),
                "high": np.array([]),
                "low": np.array([]),
                "close": np.array([]),
                "volume": np.array([]),
            }

    def _identificar_padroes(self, ohlcv: dict) -> List[Dict]:
        """
        Identifica padrões de candlestick usando TA-Lib.
        """
        padroes_encontrados = []

        for nome_padrao, funcao in self._funcoes_talib.items():
            try:
                resultado = funcao(
                    ohlcv["open"], ohlcv["high"], ohlcv["low"], ohlcv["close"]
                )

                # Verifica o último candle
                if resultado[-1] != 0:
                    direcao = "LONG" if resultado[-1] > 0 else "SHORT"
                    forca = abs(resultado[-1]) / 100.0

                    # Calcula stop loss e take profit
                    if direcao == "LONG":
                        stop_loss = float(min(ohlcv["low"][-3:]))
                        take_profit = float(
                            ohlcv["close"][-1] + (ohlcv["close"][-1] - stop_loss) * 1.5
                        )
                    else:
                        stop_loss = float(max(ohlcv["high"][-3:]))
                        take_profit = float(
                            ohlcv["close"][-1] - (stop_loss - ohlcv["close"][-1]) * 1.5
                        )

                    padrao = {
                        "timestamp": datetime.datetime.fromtimestamp(
                            int(ohlcv["timestamp"][-1] / 1000)
                        ),
                        "padrao": nome_padrao,
                        "direcao": direcao,
                        "forca": round(forca, 2),
                        "confianca": round(min(forca * 1.5, 1.0), 2),
                        "preco_entrada": float(ohlcv["close"][-1]),
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "volume": float(ohlcv["volume"][-1]),
                    }
                    padroes_encontrados.append(padrao)

            except Exception as e:
                logger.error(
                    f"[{self.nome}] Erro ao processar padrão {nome_padrao}: {e}"
                )
                continue

        return padroes_encontrados

    def _detectar_padroes(self, candles: list) -> list:
        """
        Detecta padrões de candles usando os dados fornecidos e TA-Lib.

        Args:
            candles (list): Lista de candles no formato OHLCV.

        Returns:
            list: Lista de padrões detectados com informações detalhadas.
        """
        from talib import abstract

        padroes_detectados = []

        try:
            # Extrair OHLCV
            ohlcv = self._extrair_ohlcv(candles)

            # Iterar sobre os padrões disponíveis no padroes_talib.json
            for padrao in self._padroes_talib:
                nome_funcao = f"CDL{padrao.upper()}"
                if hasattr(abstract, nome_funcao):
                    funcao = getattr(abstract, nome_funcao)
                    resultado = funcao(ohlcv)

                    # Verificar o último candle para o padrão detectado
                    if resultado[-1] != 0:
                        direcao = "Alta" if resultado[-1] > 0 else "Baixa"
                        padroes_detectados.append(
                            {
                                "padrao": padrao,
                                "direcao": direcao,
                                "candle": candles[-1],
                                "forca": abs(resultado[-1]),
                            }
                        )

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao detectar padrões: {e}", exc_info=True)

        return padroes_detectados

    def _processar_dados(self, dados_completos: dict) -> dict:
        """
        Processa os dados de candles para análise.
        Requer: symbol e timeframe presentes em dados_completos.
        """
        symbol = dados_completos.get("symbol")
        timeframe = dados_completos.get("timeframe")

        # Fallback defensivo: tentar extrair de outros campos
        if not symbol:
            # Exemplo: tentar extrair de candles se houver padrão
            # symbol = ... (adicione lógica se possível)
            pass
        if not timeframe:
            # Exemplo: tentar extrair de candles se houver padrão
            # timeframe = ... (adicione lógica se possível)
            pass

        if not all([symbol, timeframe]):
            logger.error(f"[{self.nome}] Symbol ou timeframe não fornecidos.")
            return {}

        try:
            dados_crus = dados_completos.get("crus", [])
            if not dados_crus:
                logger.error(f"[{self.nome}] Dados crus não encontrados")
                return {}

            # Extrair dados OHLCV
            ohlcv = self._extrair_ohlcv(dados_crus)
            if not all(len(v) > 0 for v in ohlcv.values()):
                logger.error(f"[{self.nome}] Falha ao extrair dados OHLCV")
                return {}

            # Identificar padrões
            padroes = self._identificar_padroes(ohlcv)
            if not padroes:
                return {}

            # Adicionar symbol e timeframe aos padrões
            for padrao in padroes:
                padrao["symbol"] = symbol
                padrao["timeframe"] = timeframe

            return padroes[0]  # Retorna o padrão mais recente

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao processar dados: {e}", exc_info=True)
            return {}

    def executar(self, *args, **kwargs):
        resultado_padrao = {"padroes_candles": []}
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                return resultado_padrao
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                return resultado_padrao
            candles = dados_completos.get("crus", [])
            if not self._validar_candles(candles, symbol, timeframe):
                return resultado_padrao
            padroes = self._detectar_padroes(candles)
            logger.debug(
                f"[{self.nome}] Padrões detectados para {symbol}-{timeframe}: {padroes}"
            )
            return {"padroes_candles": padroes}
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return resultado_padrao

    def _validar_candles(self, candles, symbol: str, timeframe: str) -> bool:
        """
        Valida o formato da lista de candles.

        Args:
            candles: Lista de k-lines.
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.

        Returns:
            bool: True se válido, False caso contrário.
        """
        if not isinstance(candles, list):
            logger.error(f"[{self.nome}] candles não é uma lista: {type(candles)}")
            return False
        if len(candles) < 10:
            logger.warning(
                f"[{self.nome}] Candles insuficientes para {symbol} - {timeframe}"
            )
            return False
        for item in candles:
            if not isinstance(item, (list, tuple)) or len(item) < 5:
                logger.error(
                    f"[{self.nome}] Item inválido em candles para {symbol} - {timeframe}: {item}"
                )
                return False
            for idx in [2, 3, 4]:  # high, low, close
                try:
                    float(item[idx])
                except (TypeError, ValueError):
                    logger.error(
                        f"[{self.nome}] Valor não numérico em candles[{idx}]: {item[idx]}"
                    )
                    return False
        return True
