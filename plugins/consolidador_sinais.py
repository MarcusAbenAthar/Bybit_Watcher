"""Plugin para consolidação de sinais de múltiplos timeframes."""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger, log_rastreamento
from plugins.plugin import Plugin
from utils.config import carregar_config
import time
import hashlib

logger = get_logger(__name__)


class ConsolidadorSinais(Plugin):
    """
    Plugin para consolidação de sinais de múltiplos timeframes.
    - Responsabilidade única: consolidar sinais em um único sinal acionável
    - Modular e configurável
    - Documentado e testável
    """

    PLUGIN_NAME = "consolidador_sinais"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sinais", "consolidacao", "analise"]
    PLUGIN_PRIORIDADE = 90

    @property
    def plugin_tabelas(self) -> dict:
        """
        Define a tabela de sinais consolidados para rastreabilidade e auditoria.
        """
        return {
            "sinais_consolidados": {
                "descricao": "Armazena sinais consolidados de múltiplos timeframes, incluindo faixas, SL/TP, score, contexto, observações e rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "direcao": "VARCHAR(10) NOT NULL",
                    "entrada_min": "DECIMAL(18,8) NOT NULL",
                    "entrada_max": "DECIMAL(18,8) NOT NULL",
                    "tp1": "DECIMAL(18,8) NOT NULL",
                    "tp2": "DECIMAL(18,8) NOT NULL",
                    "sl": "DECIMAL(18,8) NOT NULL",
                    "alavancagem": "INTEGER NOT NULL",
                    "confianca": "DECIMAL(5,2) NOT NULL",
                    "timeframes_concordantes": "INTEGER NOT NULL",
                    "diff_pontuacao": "DECIMAL(5,2) NOT NULL",
                    "forca": "VARCHAR(10) NOT NULL",
                    "volume_rel": "DECIMAL(10,2) NOT NULL",
                    "rsi": "DECIMAL(5,2)",
                    "tendencia": "VARCHAR(10)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "detalhes": "JSONB",
                    "ultima_atualizacao": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    def __init__(self, **kwargs):
        """Inicializa o ConsolidadorSinais."""
        super().__init__(**kwargs)
        self.logger = get_logger(__name__)
        self._ultimo_sinal = {}
        self._contador_sinais = {}

        # Carrega configuração
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("consolidador_sinais", {}).copy()
            if "plugins" in config and "consolidador_sinais" in config["plugins"]
            else {}
        )

        # Pesos por timeframe
        self.pesos_timeframe = self._config.get(
            "pesos_timeframe", {"4h": 0.4, "1h": 0.3, "15m": 0.2, "5m": 0.1}
        )

    def executar(self, **kwargs) -> dict:
        """
        Executa a consolidação de sinais de múltiplos timeframes.

        Args:
            **kwargs: Argumentos nomeados que podem incluir:
                - dados_completos: Dicionário contendo os dados de todos os timeframes
                - symbol: Símbolo do par (opcional, será extraído dos dados se não fornecido)

        Returns:
            dict: Dicionário com o sinal consolidado ou dados originais se não houver sinal
        """
        try:
            # Extrai os argumentos
            dados_completos = kwargs.get("dados_completos", {})
            symbol = kwargs.get("symbol")

            # Se dados_completos não foi fornecido, tenta usar os dados do kwargs
            if not dados_completos:
                dados_completos = kwargs

            # Extrai o símbolo e os timeframes
            if not symbol:
                symbol = dados_completos.get("symbol")

            # Extrai os timeframes do dados_completos
            timeframes = {}
            if "timeframes" in dados_completos:
                timeframes = dados_completos["timeframes"]
            else:
                # Tenta extrair timeframes do buffer
                for tf in ["5m", "15m", "1h", "4h"]:
                    if f"{symbol}-{tf}" in dados_completos:
                        timeframes[tf] = dados_completos[f"{symbol}-{tf}"]

            if not symbol or not timeframes:
                logger.error(
                    f"[consolidador_sinais] Symbol ou timeframes não fornecidos. Symbol: {symbol}, Timeframes: {list(timeframes.keys())}"
                )
                return dados_completos

            # Extrai sinais de cada timeframe
            sinais = self._extrair_sinais(timeframes)

            # Valida se há sinais suficientes
            if not self._validar_sinais(sinais):
                return dados_completos

            # Consolida os sinais
            sinal_consolidado = self._consolidar_sinais(sinais=sinais, symbol=symbol)

            # Verifica se é um novo sinal
            if not self._verificar_novo_sinal(sinal_consolidado):
                return dados_completos

            # Adiciona o sinal consolidado ao dicionário original
            dados_completos["sinal_consolidado"] = sinal_consolidado

            return dados_completos

        except Exception as e:
            logger.error(
                f"[consolidador_sinais] Erro ao consolidar sinais: {e}", exc_info=True
            )
            return kwargs.get("dados_completos", kwargs)

    def _extrair_sinais(self, timeframes: dict) -> dict:
        """
        Extrai sinais de cada timeframe.

        Args:
            timeframes: Dicionário com dados de cada timeframe

        Returns:
            dict: Dicionário com sinais extraídos por timeframe
        """
        sinais = {}

        for tf, dados in timeframes.items():
            # Primeiro tenta extrair do sinal consolidado
            sinal = dados.get("sinal_consolidado")

            # Se não houver sinal consolidado, tenta extrair da análise de mercado
            if not sinal:
                analise = dados.get("analise_mercado", {})
                if analise:
                    sinal = {
                        "direcao": analise.get("direcao"),
                        "forca": analise.get("forca"),
                        "confianca": analise.get("confianca"),
                        "preco_atual": analise.get("preco_atual"),
                        "volume": analise.get("volume"),
                        "rsi": analise.get("rsi"),
                        "tendencia": analise.get("tendencia"),
                        "suporte": analise.get("suporte"),
                        "resistencia": analise.get("resistencia"),
                        "atr": analise.get("atr"),
                    }

            if sinal:
                sinais[tf] = sinal
                logger.debug(f"[consolidador_sinais] Sinal extraído para {tf}: {sinal}")

        return sinais

    def _validar_sinais(self, sinais: dict) -> bool:
        """
        Valida se há sinais suficientes para consolidar.

        Args:
            sinais: Dicionário com sinais por timeframe

        Returns:
            bool: True se os sinais são válidos, False caso contrário
        """
        if not sinais:
            logger.error("[consolidador_sinais] Nenhum sinal encontrado")
            return False

        # Verifica se tem os timeframes principais
        timeframes_principais = ["4h", "1h"]
        if not all(tf in sinais for tf in timeframes_principais):
            logger.error(
                f"[consolidador_sinais] Faltam timeframes principais: {timeframes_principais}"
            )
            return False

        # Verifica se cada sinal tem direção
        for tf, sinal in sinais.items():
            if not sinal.get("direcao"):
                logger.error(f"[consolidador_sinais] Sinal sem direção para {tf}")
                return False

        return True

    def _calcular_media_forca_confiança(self, sinais):
        mapa_forca = {"fraca": 0.2, "media": 0.5, "forte": 1.0}
        mapa_confianca = {"baixa": 0.2, "media": 0.5, "alta": 1.0}

        somatorio_forca = 0
        somatorio_confianca = 0
        total = 0

        for sinal in sinais:
            forca = mapa_forca.get(sinal.get("forca", "").lower(), 0)
            confianca = mapa_confianca.get(sinal.get("confianca", "").lower(), 0)
            somatorio_forca += forca
            somatorio_confianca += confianca
            total += 1

        media_forca = somatorio_forca / total if total else 0
        media_confianca = somatorio_confianca / total if total else 0

        return media_forca, media_confianca

    def _gerar_hash_sinal(self, sinal: dict) -> str:
        base_str = f"{sinal['symbol']}_{sinal['direcao']}_{sinal['preco_atual']}_{sorted(sinal['timeframes'])}"
        return hashlib.sha256(base_str.encode()).hexdigest()

    def _determinar_direcao(self, sinais):
        direcoes = [s["direcao"] for s in sinais]
        long_count = direcoes.count("LONG")
        short_count = direcoes.count("SHORT")

        if abs(long_count - short_count) >= 2:
            return "LONG" if long_count > short_count else "SHORT"
        return "LATERAL"

    def _consolidar_sinais(self, sinais: dict, symbol: str) -> dict:
        """
        Consolida os sinais de múltiplos timeframes em um único sinal.

        Args:
            sinais (dict): Dicionário com sinais por timeframe
            symbol (str): Símbolo do par

        Returns:
            dict: Sinal consolidado ou None se inválido
        """
        if not sinais or not symbol:
            logger.error(
                f"[consolidador_sinais] Sinais ou symbol não fornecidos: sinais={bool(sinais)}, symbol={symbol}"
            )
            return None

        # Lista para armazenar os sinais processados
        sinais_processados = []

        # Processa cada timeframe
        for tf, sinal in sinais.items():
            if not isinstance(sinal, dict):
                logger.error(f"[consolidador_sinais] Sinal inválido para {tf}: {sinal}")
                continue

            sinal_processado = {
                "timeframe": tf,
                "symbol": symbol,
                "direcao": sinal.get("direcao"),
                "forca": sinal.get("forca"),
                "confianca": sinal.get("confianca"),
                "preco_atual": sinal.get("preco_atual"),
            }
            sinais_processados.append(sinal_processado)

        if not sinais_processados:
            logger.error("[consolidador_sinais] Nenhum sinal válido para processar")
            return None

        # Determina a direção final com base nos sinais
        direcao_final = self._determinar_direcao(sinais_processados)
        if direcao_final == "LATERAL":
            logger.debug("[consolidador_sinais] Direção final é LATERAL")
            return None

        # Calcula a média de força e confiança
        media_forca, media_confianca = self._calcular_media_forca_confiança(
            sinais_processados
        )

        # Obtém o preço atual do último sinal
        preco_atual = sinais_processados[-1]["preco_atual"]

        # Monta o sinal consolidado
        sinal_consolidado = {
            "symbol": symbol,
            "direcao": direcao_final,
            "preco_atual": preco_atual,
            "timeframes": list(sinais.keys()),
            "forca": round(media_forca, 2),
            "confianca": round(media_confianca, 2),
        }

        # Gera o hash do sinal e verifica se já foi emitido
        hash_sinal = self._gerar_hash_sinal(sinal_consolidado)
        if hash_sinal in self._ultimo_sinal:
            logger.debug(f"[consolidador_sinais] Sinal duplicado: {hash_sinal}")
            return None

        logger.info(
            f"[consolidador_sinais] Sinal consolidado gerado: {sinal_consolidado}"
        )
        return sinal_consolidado

    def _verificar_novo_sinal(self, sinal: dict) -> bool:
        """
        Verifica se o sinal é novo ou duplicado.

        Args:
            sinal: Sinal a ser verificado

        Returns:
            bool: True se o sinal é novo, False se é duplicado
        """
        if not sinal:
            return False

        # Gera hash do sinal
        sinal_str = f"{sinal['symbol']}_{sinal['direcao']}_{sinal['preco_atual']}"
        sinal_hash = hashlib.md5(sinal_str.encode()).hexdigest()

        # Limpa sinais antigos (mais de 5 minutos)
        agora = time()
        self._ultimo_sinal = {
            k: v for k, v in self._ultimo_sinal.items() if agora - v["timestamp"] < 300
        }

        # Verifica se o sinal já existe
        if sinal_hash in self._ultimo_sinal:
            logger.debug(f"[consolidador_sinais] Sinal duplicado: {sinal_str}")
            return False

        # Registra novo sinal
        self._ultimo_sinal[sinal_hash] = {"sinal": sinal, "timestamp": agora}

        return True
