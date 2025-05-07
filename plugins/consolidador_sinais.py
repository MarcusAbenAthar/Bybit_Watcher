"""
Plugin de consolidador de sinais.
Responsabilidade única: consolidar sinais de múltiplos timeframes/plugins.
Não deve registrar, inicializar ou finalizar automaticamente.
Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
"""

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

        # Permitir consolidação com pelo menos 1 timeframe válido
        if len(sinais) < 1:
            logger.error(
                f"[consolidador_sinais] Menos de 1 timeframe válido para consolidar."
            )
            return False

        # Verifica se cada sinal tem direção
        for tf, sinal in sinais.items():
            if not sinal.get("direcao"):
                logger.error(f"[consolidador_sinais] Sinal sem direção para {tf}")
                return False

        return True

    def _calcular_media_forca_confiança(self, sinais):
        """
        Calcula a média ponderada de força e confiança considerando os pesos dos timeframes.
        """
        mapa_forca = {"FRACA": 0.2, "MÉDIA": 0.5, "FORTE": 1.0}
        mapa_confianca = {"BAIXA": 0.2, "MÉDIA": 0.5, "ALTA": 1.0}

        somatorio_forca = 0
        somatorio_confianca = 0
        total_peso = 0

        for sinal in sinais:
            tf = sinal.get("timeframe")
            peso = self.pesos_timeframe.get(tf, 0.1)  # Peso padrão 0.1 se não definido

            forca = mapa_forca.get(str(sinal.get("forca", "FRACA")).upper(), 0.2)
            confianca = (
                float(sinal.get("confianca", 0.0)) / 100.0
            )  # Converte de % para decimal

            somatorio_forca += forca * peso
            somatorio_confianca += confianca * peso
            total_peso += peso

        if total_peso == 0:
            return 0.2, 0.0  # Valores padrão se não houver sinais

        media_forca = somatorio_forca / total_peso
        media_confianca = somatorio_confianca / total_peso

        # Converte força numérica para texto
        if media_forca >= 0.75:
            forca_final = "FORTE"
        elif media_forca >= 0.4:
            forca_final = "MÉDIA"
        else:
            forca_final = "FRACA"

        return forca_final, round(
            media_confianca * 100, 2
        )  # Converte confiança de volta para %

    def _gerar_hash_sinal(self, sinal: dict) -> str:
        base_str = f"{sinal['symbol']}_{sinal['direcao']}_{sinal['preco_atual']}_{sorted(sinal['timeframes'])}"
        return hashlib.sha256(base_str.encode()).hexdigest()

    def _determinar_direcao(self, sinais):
        """
        Determina a direção final com base nos sinais dos timeframes, considerando os pesos.
        """
        peso_alta = 0
        peso_baixa = 0
        total_peso = 0

        for sinal in sinais:
            tf = sinal.get("timeframe")
            peso = self.pesos_timeframe.get(tf, 0.1)  # Peso padrão 0.1 se não definido
            direcao = str(sinal.get("direcao", "LATERAL")).upper()

            if direcao in ["ALTA", "LONG"]:
                peso_alta += peso
            elif direcao in ["BAIXA", "SHORT"]:
                peso_baixa += peso
            total_peso += peso

        if total_peso == 0:
            return "LATERAL"

        # Calcula a diferença percentual
        diff = abs(peso_alta - peso_baixa) / total_peso

        # Se a diferença for significativa (>20%), retorna a direção dominante
        if diff > 0.2:
            return "ALTA" if peso_alta > peso_baixa else "BAIXA"

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
                "stop_loss": sinal.get("stop_loss"),
                "take_profit": sinal.get("take_profit"),
                "alavancagem": sinal.get("alavancagem"),
            }
            sinais_processados.append(sinal_processado)

        if not sinais_processados:
            logger.error("[consolidador_sinais] Nenhum sinal válido para processar")
            return None

        # Determina a direção final com base nos sinais
        direcao_final = self._determinar_direcao(sinais_processados)
        logger.debug(f"[consolidador_sinais] Direção final é {direcao_final}")

        # Calcula a média de força e confiança
        forca_final, confianca_final = self._calcular_media_forca_confiança(
            sinais_processados
        )

        # Calcula SL/TP e alavancagem ponderados
        sl_final = 0
        tp_final = 0
        alavancagem_final = 0
        total_peso = 0

        for sinal in sinais_processados:
            tf = sinal.get("timeframe")
            peso = self.pesos_timeframe.get(tf, 0.1)

            sl = float(sinal.get("stop_loss", 0) or 0)
            tp = float(sinal.get("take_profit", 0) or 0)
            alav = float(sinal.get("alavancagem", 0) or 0)

            sl_final += sl * peso
            tp_final += tp * peso
            alavancagem_final += alav * peso
            total_peso += peso

        if total_peso > 0:
            sl_final = round(sl_final / total_peso, 8)
            tp_final = round(tp_final / total_peso, 8)
            alavancagem_final = round(alavancagem_final / total_peso, 2)

        # Obtém o preço atual do último sinal
        preco_atual = sinais_processados[-1]["preco_atual"]

        # Monta o sinal consolidado
        sinal_consolidado = {
            "symbol": symbol,
            "direcao": direcao_final,
            "preco_atual": preco_atual,
            "timeframes": list(sinais.keys()),
            "forca": forca_final,
            "confianca": confianca_final,
            "stop_loss": sl_final,
            "take_profit": tp_final,
            "alavancagem": alavancagem_final,
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
        agora = time.time()
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
