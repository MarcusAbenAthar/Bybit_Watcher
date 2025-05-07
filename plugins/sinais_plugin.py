"""
Plugin de sinais.
Responsabilidade única: geração e análise de sinais de trading.
Não deve registrar, inicializar ou finalizar automaticamente.
Toda a lógica de ciclo de vida é centralizada no GerenciadorPlugins.
"""

from utils.logging_config import get_logger, log_rastreamento
from plugins.plugin import Plugin
import logging
from copy import deepcopy
import numpy as np
from utils.config import carregar_config
from utils.plugin_utils import validar_klines, padronizar_direcao

logger = get_logger(__name__)
logger_sinais = logging.getLogger("sinais")


class SinaisPlugin(Plugin):
    """
    Plugin para consolidação de dados de análise e geração do sinal final
    com SL/TP, confiança e alavancagem.
    - Responsabilidade única: consolidação de sinais multi-timeframe.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sinais", "consolidador", "analise"]
    PLUGIN_PRIORIDADE = 100

    _RESULTADO_PADRAO = {
        "analise_mercado": {
            "direcao": "LATERAL",
            "forca": "FRACA",
            "confianca": 0.0,
            "preco_atual": 0.0,
            "volume": 0.0,
            "rsi": 50.0,
            "tendencia": "LATERAL",
            "suporte": 0.0,
            "resistencia": 0.0,
            "atr": 0.0,
        }
    }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "sinais_gerados": {
                "descricao": "Armazena sinais finais gerados pelo bot, incluindo faixas de entrada, SL/TP, score, contexto, observações e candle bruto para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "direcao": "VARCHAR(10) NOT NULL",
                    "forca": "VARCHAR(10)",
                    "confianca": "DECIMAL(5,2) NOT NULL",
                    "preco_entrada": "DECIMAL(18,8) NOT NULL",
                    "faixa_entrada_min": "DECIMAL(18,8)",
                    "faixa_entrada_max": "DECIMAL(18,8)",
                    "stop_loss": "DECIMAL(18,8) NOT NULL",
                    "take_profit": "DECIMAL(18,8) NOT NULL",
                    "volume": "DECIMAL(18,8)",
                    "alavancagem": "INTEGER NOT NULL",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "status": "VARCHAR(20) NOT NULL",
                    "resultado": "DECIMAL(18,8)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
            "analises_consolidadas": {
                "descricao": "Armazena análises intermediárias consolidadas, valores, pesos, contexto, observações e candle para rastreabilidade.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "tipo_analise": "VARCHAR(50) NOT NULL",
                    "valor": "DECIMAL(18,8)",
                    "direcao": "VARCHAR(10)",
                    "peso": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            },
        }

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin SinaisPlugin.
        """
        return [
            "gerenciador_banco",
            "indicadores_tendencia",
            "indicadores_osciladores",
            "indicadores_volume",
            "calculo_alavancagem",
            "calculo_risco",
        ]

    def consolidar_sinais_multi_timeframe(
        self, sinais_timeframes: dict, symbol: str, config: dict
    ) -> dict:
        """
        Consolida sinais de múltiplos timeframes para um único sinal final, usando pesos definidos em config.
        Args:
            sinais_timeframes (dict): Dict[timeframe, dict_sinal]
            symbol (str): Símbolo do par
            config (dict): Configuração global do bot
        Returns:
            dict: Sinal único consolidado para o ativo
        """
        try:
            pesos_timeframe = config.get("PESOS_TIMEFRAME", {})
            direcoes = {"LONG": 1, "SHORT": -1, "LATERAL": 0}
            soma_pesos = 0.0
            soma_direcao = 0.0
            soma_confianca = 0.0
            soma_forca = 0.0
            soma_alavancagem = 0.0
            soma_sl = 0.0
            soma_tp = 0.0
            n_validos = 0
            for tf, sinal in sinais_timeframes.items():
                peso = pesos_timeframe.get(tf, 0.0)
                if not sinal or not isinstance(sinal, dict):
                    continue
                direcao = direcoes.get(str(sinal.get("direcao", "LATERAL")).upper(), 0)
                confianca = float(sinal.get("confianca", 0.0))
                forca = (
                    1
                    if str(sinal.get("forca", "FRACA")).upper() == "FORTE"
                    else (
                        0.5
                        if str(sinal.get("forca", "FRACA")).upper() == "MEDIA"
                        or str(sinal.get("forca", "FRACA")).upper() == "MÉDIA"
                        else 0
                    )
                )
                alavancagem = float(sinal.get("alavancagem", 0.0))
                sl = float(sinal.get("stop_loss", 0.0) or 0.0)
                tp = float(sinal.get("take_profit", 0.0) or 0.0)
                soma_pesos += peso
                soma_direcao += direcao * peso
                soma_confianca += confianca * peso
                soma_forca += forca * peso
                soma_alavancagem += alavancagem * peso
                soma_sl += sl * peso
                soma_tp += tp * peso
                n_validos += 1
            if soma_pesos == 0 or n_validos == 0:
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": None,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }
            media_direcao = soma_direcao / soma_pesos
            media_confianca = soma_confianca / soma_pesos
            media_forca = soma_forca / soma_pesos
            media_alavancagem = soma_alavancagem / soma_pesos
            media_sl = soma_sl / soma_pesos
            media_tp = soma_tp / soma_pesos
            # Decisão final de direção
            if media_direcao > 0.25:
                direcao_final = "LONG"
            elif media_direcao < -0.25:
                direcao_final = "SHORT"
            else:
                direcao_final = "LATERAL"
            # Força final
            if media_forca > 0.75:
                forca_final = "FORTE"
            elif media_forca > 0.4:
                forca_final = "MÉDIA"
            else:
                forca_final = "FRACA"
            sinal_final = {
                "direcao": direcao_final,
                "forca": forca_final,
                "confianca": round(media_confianca, 2),
                "alavancagem": round(media_alavancagem, 2),
                "timestamp": None,  # Timestamp pode ser o mais recente dos timeframes
                "stop_loss": round(media_sl, 2),
                "take_profit": round(media_tp, 2),
            }
            return sinal_final
        except Exception as e:
            logger.error(f"Erro na consolidação multi-timeframe: {e}")
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
                "stop_loss": 0.0,
                "take_profit": 0.0,
            }

    def __init__(
        self,
        gerenciador_banco=None,
        indicadores_tendencia=None,
        indicadores_osciladores=None,
        indicadores_volume=None,
        calculo_alavancagem=None,
        calculo_risco=None,
        **kwargs,
    ):
        """
        Inicializa o plugin SinaisPlugin com dependências injetadas.
        """
        super().__init__(**kwargs)
        self.gerenciador_banco = gerenciador_banco
        self.indicadores_tendencia = indicadores_tendencia
        self.indicadores_osciladores = indicadores_osciladores
        self.indicadores_volume = indicadores_volume
        self.calculo_alavancagem = calculo_alavancagem
        self.calculo_risco = calculo_risco
        logger.info(
            f"[sinais_plugin] Dependências injetadas: "
            f"gerenciador_banco={gerenciador_banco is not None}, "
            f"indicadores_tendencia={indicadores_tendencia is not None}, "
            f"indicadores_osciladores={indicadores_osciladores is not None}, "
            f"indicadores_volume={indicadores_volume is not None}, "
            f"calculo_alavancagem={calculo_alavancagem is not None}, "
            f"calculo_risco={calculo_risco is not None}"
        )
        # Carrega config institucional centralizada
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("sinais_plugin", {}).copy()
            if "plugins" in config and "sinais_plugin" in config["plugins"]
            else {}
        )
        self._confianca_pesos = {
            "analise_mercado": 0.4,
            "calculo_risco": 0.3,
            "outros": 0.3,
        }
        self._confianca_min = 0.45
        self._confianca_max = 1.0
        self._ultimos_sinais = {}

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com configurações fornecidas.

        Args:
            config: Dicionário com configurações (ex.: pesos de confiança).

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            # Verifica se as dependências foram injetadas
            if not self.calculo_alavancagem:
                logger.error(f"[{self.nome}] calculo_alavancagem não foi injetado")
                return False
            if not self.calculo_risco:
                logger.error(f"[{self.nome}] calculo_risco não foi injetado")
                return False

            config_sinais = config.get("sinais_plugin", {})
            self._confianca_pesos = config_sinais.get(
                "confianca_pesos", self._confianca_pesos
            )
            self._confianca_min = config_sinais.get(
                "confianca_min", self._confianca_min
            )
            self._confianca_max = config_sinais.get(
                "confianca_max", self._confianca_max
            )

            if not isinstance(self._confianca_pesos, dict) or not all(
                isinstance(v, (int, float)) and v >= 0
                for v in self._confianca_pesos.values()
            ):
                logger.error(
                    f"[{self.nome}] confianca_pesos inválido: {self._confianca_pesos}"
                )
                return False
            if not (
                isinstance(self._confianca_min, (int, float))
                and isinstance(self._confianca_max, (int, float))
                and 0.0 <= self._confianca_min <= self._confianca_max <= 1.0
            ):
                logger.error(
                    f"[{self.nome}] Limites de confiança inválidos: min={self._confianca_min}, max={self._confianca_max}"
                )
                return False

            logger.info(
                f"[{self.nome}] inicializado com pesos: {self._confianca_pesos}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def executar(self, *args, **kwargs) -> dict:
        """
        Executa a análise de sinais e retorna SEMPRE o dicionário atualizado dados_completos.
        Garante que todos os campos essenciais (symbol, timeframe, timeframes) sejam preservados e propagados.
        """
        try:
            from utils.logging_config import log_rastreamento

            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            dados_completos = kwargs.get("dados_completos")
            log_rastreamento(
                componente=f"sinais_plugin/{symbol}-{timeframe}",
                acao="entrada",
                detalhes=f"chaves={list(dados_completos.keys()) if isinstance(dados_completos, dict) else dados_completos}",
            )

            if not dados_completos or not isinstance(dados_completos, dict):
                logger.error(f"[{self.nome}] dados_completos não fornecido ou inválido")
                return kwargs.get("dados_completos", {})

            if not symbol:
                logger.error(f"[{self.nome}] Symbol não fornecido")
                return dados_completos

            if not timeframe:
                logger.error(f"[{self.nome}] Timeframe não fornecido")
                return dados_completos

            # Processar análise de mercado
            analise_mercado = self._processar_analise_mercado(dados_completos)
            dados_completos["analise_mercado"] = analise_mercado

            # Ao consolidar analise_mercado, padronizar direção
            analise_mercado["direcao"] = padronizar_direcao(
                analise_mercado.get("direcao", "LATERAL")
            )

            # Propagar campos essenciais para a saída (garantia de rastreabilidade)
            campos_essenciais = ["preco_atual", "atr", "suporte", "resistencia"]
            for campo in campos_essenciais:
                if campo in dados_completos:
                    analise_mercado[campo] = dados_completos[campo]

            logger_sinais.info(
                f"[{symbol} - {timeframe}] "
                f"DIREÇÃO: {analise_mercado['direcao']} | "
                f"FORÇA: {analise_mercado['forca']} | "
                f"CONFIANÇA: {analise_mercado['confianca']:.2f}% | "
                f"TENDÊNCIA: {analise_mercado['tendencia']} | "
                f"VOL REL: {analise_mercado['volume']['rel']:.2f} | "
                f"ATR: {analise_mercado.get('atr')} | PRECO_ATUAL: {analise_mercado.get('preco_atual')} | SUPORTE: {analise_mercado.get('suporte')} | RESISTENCIA: {analise_mercado.get('resistencia')}"
            )

            log_rastreamento(
                componente=f"sinais_plugin/{symbol}-{timeframe}",
                acao="saida",
                detalhes=f"sinais_gerados={dados_completos.get('sinais_gerados', {})} | analise_mercado={analise_mercado}",
            )

            return dados_completos

        except Exception as e:
            logger.error(f"[{self.nome}] Erro na execução: {e}", exc_info=True)
            return kwargs.get("dados_completos", {})

    def _processar_analise_mercado(self, dados: dict) -> dict:
        """
        Processa os dados de análise de mercado, ponderando volume, tendência, RSI e logando decisões.
        Agora considera todas as métricas de volume disponíveis.
        """
        try:
            analise = dados.get("analise_mercado", {})
            if not analise:
                analise = deepcopy(self._RESULTADO_PADRAO["analise_mercado"])
            rsi = float(dados.get("rsi", {}).get("valor", 50.0))
            volume_dict = dados.get("volume", {}) or {}
            obv = float(volume_dict.get("obv", 0.0) or 0.0)
            cmf = float(volume_dict.get("cmf", 0.0) or 0.0)
            mfi = float(volume_dict.get("mfi", 0.0) or 0.0)
            volume_rel = (
                (abs(obv) + abs(cmf) + abs(mfi)) / 3 if any([obv, cmf, mfi]) else 0.0
            )
            volume_fator = self._volume_acima_media(dados.get("crus", []), n=20)
            tendencia = self._determinar_tendencia(dados)

            # NOVO: Coletar sinais dos outros plugins
            sinais_plugins = []
            for plugin in ["price_action", "medias_moveis", "analise_candles"]:
                info = dados.get(plugin, {})
                if isinstance(info, dict) and info.get("direcao") and info.get("forca"):
                    sinais_plugins.append(
                        {
                            "direcao": str(info["direcao"]).upper(),
                            "forca": str(info["forca"]).upper(),
                            "confianca": float(info.get("confianca", 0.0)),
                        }
                    )

            # Se houver convergência clara de ALTA ou BAIXA, priorizar
            direcoes = [s["direcao"] for s in sinais_plugins]
            if direcoes.count("ALTA") > 1:
                direcao = "ALTA"
            elif direcoes.count("BAIXA") > 1:
                direcao = "BAIXA"
            else:
                direcao = analise.get("direcao", "LATERAL")

            # Força: se maioria for FORTE ou MÉDIA, refletir
            forcas = [s["forca"] for s in sinais_plugins]
            if forcas.count("FORTE") > 1:
                forca = "FORTE"
            elif forcas.count("MÉDIA") > 1:
                forca = "MÉDIA"
            else:
                forca = analise.get("forca", "FRACA")

            # Confiança: média das confianças dos plugins + ajuste se houver convergência
            confiancas = [s["confianca"] for s in sinais_plugins if s["confianca"] > 0]
            if confiancas:
                confianca = sum(confiancas) / len(confiancas)
                if direcao in ["ALTA", "BAIXA"] and forca in ["MÉDIA", "FORTE"]:
                    confianca = min(1.0, confianca + 0.2)
            else:
                confianca = float(analise.get("confianca", 0.0))

            logger.info(
                f"[sinais_plugin] Decisão FINAL: DIREÇÃO={direcao}, FORÇA={forca}, RSI={rsi}, OBV={obv}, CMF={cmf}, MFI={mfi}, TENDÊNCIA={tendencia}, CONFIANÇA={confianca}"
            )
            campos_essenciais = ["atr", "preco_atual", "suporte", "resistencia"]
            analise_corrigida = dict(analise)
            for campo in campos_essenciais:
                valor_raiz = dados.get(campo)
                valor_analise = analise_corrigida.get(campo, None)
                if valor_raiz not in (None, 0.0):
                    analise_corrigida[campo] = valor_raiz
                elif valor_analise not in (None, 0.0):
                    analise_corrigida[campo] = valor_analise
                else:
                    analise_corrigida[campo] = 0.0
            analise_corrigida["direcao"] = direcao
            analise_corrigida["forca"] = forca
            analise_corrigida["confianca"] = round(confianca, 2)
            return {
                "direcao": analise_corrigida.get("direcao"),
                "forca": analise_corrigida.get("forca"),
                "confianca": analise_corrigida.get("confianca"),
                "preco_atual": float(analise_corrigida.get("preco_atual", 0.0)),
                "volume": {"obv": obv, "cmf": cmf, "mfi": mfi, "rel": volume_rel},
                "rsi": rsi,
                "tendencia": tendencia,
                "suporte": float(analise_corrigida.get("suporte", 0.0)),
                "resistencia": float(analise_corrigida.get("resistencia", 0.0)),
                "atr": float(analise_corrigida.get("atr", 0.0)),
            }
        except Exception as e:
            logger.error(f"Erro ao processar análise de mercado: {e}")
            return deepcopy(self._RESULTADO_PADRAO["analise_mercado"])

    def _determinar_tendencia(self, dados: dict) -> str:
        """
        Determina a tendência com base nos indicadores.
        """
        try:
            # Análise de médias móveis
            ma_curta = dados.get("ma_curta", {}).get("valor", 0.0)
            ma_media = dados.get("ma_media", {}).get("valor", 0.0)
            ma_longa = dados.get("ma_longa", {}).get("valor", 0.0)

            if not all([ma_curta, ma_media, ma_longa]):
                return "LATERAL"

            # Verificar alinhamento das médias
            if ma_curta > ma_media > ma_longa:
                return "ALTA"
            elif ma_curta < ma_media < ma_longa:
                return "BAIXA"

            # Análise de momentum
            rsi = float(dados.get("rsi", {}).get("valor", 50.0))
            if rsi >= 70:
                return "ALTA"
            elif rsi <= 30:
                return "BAIXA"

            return "LATERAL"

        except Exception as e:
            logger.error(f"Erro ao determinar tendência: {e}")
            return "LATERAL"

    def _calcular_forca(
        self,
        forca_base: str,
        rsi: float,
        volume_rel: float,
        tendencia: str,
        volume_fator: float = 1.0,
    ) -> str:
        """
        Calcula a força do sinal com base em múltiplos indicadores e fator de volume.
        """
        pontos = 0
        # Pontos por RSI
        if 20 <= rsi <= 30 or 70 <= rsi <= 80:
            pontos += 2
        elif 30 < rsi < 40 or 60 < rsi < 70:
            pontos += 1
        # Pontos por volume
        if volume_fator >= 1.0:
            pontos += 2
        elif volume_fator >= 0.7:
            pontos += 1
        # Pontos por tendência
        if tendencia != "LATERAL":
            pontos += 1
        # Determinar força final
        if pontos >= 4:
            return "FORTE"
        elif pontos >= 2:
            return "MÉDIA"
        return "FRACA"

    def _ajustar_confianca(
        self, base: float, rsi: float, volume_rel: float, tendencia: str, direcao: str
    ) -> float:
        """
        Ajusta a confiança base com base em múltiplos fatores.
        """
        try:
            confianca = base

            # Ajuste por RSI
            if (direcao == "LONG" and rsi <= 30) or (direcao == "SHORT" and rsi >= 70):
                confianca *= 1.2  # +20%
            elif (direcao == "LONG" and rsi >= 70) or (
                direcao == "SHORT" and rsi <= 30
            ):
                confianca *= 0.8  # -20%

            # Ajuste por volume
            if volume_rel >= 2.0:
                confianca *= 1.15  # +15%
            elif volume_rel <= 0.5:
                confianca *= 0.85  # -15%

            # Ajuste por tendência
            if tendencia != "LATERAL":
                if (direcao == "LONG" and tendencia == "ALTA") or (
                    direcao == "SHORT" and tendencia == "BAIXA"
                ):
                    confianca *= 1.1  # +10%
                else:
                    confianca *= 0.9  # -10%

            return round(
                min(max(confianca, self._confianca_min), self._confianca_max), 2
            )

        except Exception as e:
            logger.error(f"Erro ao ajustar confiança: {e}")
            return self._confianca_min

    def _volume_acima_media(self, candles: list, n: int = 20) -> float:
        """
        Retorna um fator de ajuste baseado no volume do candle mais recente em relação à média dos últimos n candles.
        1.0 se acima da média, 0.7 se igual, 0.5 se abaixo.
        """
        try:
            if not candles or len(candles) < n + 1:
                return 0.5
            volumes = [float(c[5]) for c in candles[-(n + 1) :]]
            media = sum(volumes[:-1]) / n
            if volumes[-1] > media:
                return 1.0
            elif abs(volumes[-1] - media) / media < 0.1:
                return 0.7
            else:
                return 0.5
        except Exception as e:
            logger.error(f"[sinais_plugin] Erro ao validar volume: {e}")
            return 0.5

    def _preco_acima_media(self, candles: list, periodo: int = 20) -> bool:
        """
        Retorna True se o preço de fechamento atual está acima da média móvel simples dos últimos 'periodo' candles.
        """
        try:
            if not candles or len(candles) < periodo:
                return False
            closes = [float(c[4]) for c in candles[-periodo:]]
            return closes[-1] > (sum(closes[:-1]) / (periodo - 1))
        except Exception as e:
            logger.error(f"[sinais_plugin] Erro ao validar média móvel: {e}")
            return False

    def _proximo_resistencia(
        self, close: float, resistencias: list, margem: float = 0.001
    ) -> bool:
        """
        Retorna True se o preço de fechamento está muito próximo de uma resistência.
        """
        try:
            for r in resistencias:
                if abs(close - r) / close < margem:
                    return True
            return False
        except Exception as e:
            logger.error(f"[sinais_plugin] Erro ao validar resistência: {e}")
            return False

    def _gerar_sinal(self, dados: dict, symbol: str, timeframe: str) -> dict:
        """
        Gera o sinal final consolidado.

        Args:
            dados: Dicionário com dados de análise.
            symbol: Símbolo do par.
            timeframe: Timeframe.

        Returns:
            dict: Sinal com direção, força, confiança, alavancagem, SL/TP, timestamp.
        """
        try:
            analise = dados.get("analise_mercado", {})
            # Padronização da direção para 'LONG'/'SHORT' e confiança em porcentagem
            direcao_original = analise.get("direcao", "LATERAL")
            forca = analise.get("forca", "FRACA")
            confianca_base = analise.get("confianca", 0.0)

            # Conversão da direção
            if direcao_original == "ALTA":
                direcao = "LONG"
            elif direcao_original == "BAIXA":
                direcao = "SHORT"
            else:
                direcao = "LATERAL"

            confianca = self._calcular_confianca(
                dados, direcao_original, confianca_base
            )
            confianca_pct = round(confianca * 100, 2)
            alavancagem = self._calcular_alavancagem(dados, direcao, confianca)
            stop_loss, take_profit = self._extrair_sl_tp(dados, direcao)
            timestamp = self._extrair_timestamp(dados)

            # Filtro de confiança mínima
            confianca_min = (
                self._confianca_min if hasattr(self, "_confianca_min") else 0.6
            )
            if confianca < confianca_min:
                logger.info(
                    f"[sinais_plugin] Sinal descartado por confiança baixa: {confianca:.2f}"
                )
                return None

            # Filtro de volume relativo
            candles = dados.get("crus", [])
            if not self._volume_acima_media(candles, n=20):
                logger.info(
                    f"[sinais_plugin] Sinal descartado por volume abaixo da média."
                )
                return None

            # Validação de contexto: preço acima da média móvel
            if direcao == "LONG" and not self._preco_acima_media(candles, periodo=20):
                logger.info(
                    f"[sinais_plugin] Sinal LONG descartado: preço não está acima da média móvel."
                )
                return None

            # Validação de resistência (exemplo usando candles, pode ser extendido)
            close = float(candles[-1][4]) if candles else 0.0
            resistencias = []
            if "pivots" in dados and isinstance(dados["pivots"], dict):
                resistencias = dados["pivots"].get("resistencias", [])
            if self._proximo_resistencia(close, resistencias, margem=0.0015):
                logger.info(
                    f"[sinais_plugin] Sinal descartado: preço próximo de resistência relevante."
                )
                return None

            # Correção: nunca retornar None para SL/TP
            if stop_loss is None:
                stop_loss = 0.0
            if take_profit is None:
                take_profit = 0.0

            sinal = {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca_pct,  # Agora em porcentagem
                "alavancagem": alavancagem,
                "timestamp": timestamp,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

            logger_sinais.info(
                f"[{symbol} - {timeframe}] DIREÇÃO: {direcao} | FORÇA: {forca} | "
                f"CONFIANÇA: {confianca_pct:.2f}% | ALAVANCAGEM: {alavancagem:.2f}x | "
                f"SL: {stop_loss} | TP: {take_profit}"
            )

            return sinal
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao gerar sinal: {e}", exc_info=True)
            return None

    def _calcular_confianca(self, dados: dict, direcao: str, base: float) -> float:
        """
        Consolida as confiabilidades dos plugins com base na direção.
        Retorna confiança como float (0.0 a 1.0), mas será convertida para porcentagem na saída final.
        """
        try:
            confiancas = []
            ajuste = 0.0

            # Peso para analise_mercado
            confianca_analise = dados.get("analise_mercado", {}).get("confianca", 0.0)
            if confianca_analise > 0:
                confiancas.append(
                    (
                        confianca_analise,
                        self._confianca_pesos.get("analise_mercado", 0.4),
                    )
                )

            # Peso para calculo_risco
            if self.calculo_risco and dados.get("calculo_risco"):
                confianca_risco = dados["calculo_risco"].get("confianca", 0.0)
                dir_risco = dados["calculo_risco"].get("direcao", "LATERAL")
                if confianca_risco > 0:
                    confiancas.append(
                        (
                            confianca_risco,
                            self._confianca_pesos.get("calculo_risco", 0.3),
                        )
                    )
                    if dir_risco == direcao:
                        ajuste += 0.1
                    elif dir_risco != "LATERAL":
                        ajuste -= 0.1

            # Outros plugins
            for chave, info in dados.items():
                if chave not in [
                    "analise_mercado",
                    "calculo_risco",
                    "crus",
                    "sinais",
                ] and isinstance(info, dict):
                    c = info.get("confianca", 0.0)
                    if c > 0:
                        confiancas.append(
                            (
                                c,
                                self._confianca_pesos.get("outros", 0.3)
                                / max(1, len(dados) - 3),
                            )
                        )
                        dir_info = info.get("direcao", "LATERAL")
                        if dir_info == direcao:
                            ajuste += 0.05
                        elif dir_info != "LATERAL":
                            ajuste -= 0.05

            # Calcular média ponderada
            if confiancas:
                total_peso = sum(peso for _, peso in confiancas)
                if total_peso > 0:
                    media = sum(c * peso for c, peso in confiancas) / total_peso
                else:
                    media = sum(c for c, _ in confiancas) / len(confiancas)
            else:
                media = 0.0

            resultado = base * (1 + ajuste)
            resultado = (resultado + media) / 2 if confiancas else resultado
            return round(
                min(max(resultado, self._confianca_min), self._confianca_max), 4
            )  # Mais precisão interna
        except Exception as e:
            logger.error(
                f"[{self.nome}] Erro ao calcular confiança: {e}", exc_info=True
            )
            return 0.0

    def _calcular_alavancagem(
        self, dados: dict, direcao: str, confianca: float
    ) -> float:
        """
        Calcula a alavancagem delegando ao plugin CalculoAlavancagem.

        Args:
            dados: Dicionário com dados de análise.
            direcao: Direção do sinal.
            confianca: Confiança consolidada.

        Returns:
            float: Valor da alavancagem.
        """
        if not self.calculo_alavancagem:
            logger.warning(
                f"[{self.nome}] Plugin de cálculo de alavancagem não disponível"
            )
            return 0.0

        try:
            return self.calculo_alavancagem.calcular_alavancagem(
                crus=dados.get("crus", []), direcao=direcao, confianca=confianca
            )
        except Exception as e:
            logger.warning(f"[{self.nome}] Erro ao calcular alavancagem: {e}")
            return 0.0

    def _extrair_sl_tp(self, dados: dict, direcao: str) -> tuple:
        """
        Extrai stop-loss e take-profit dos padrões de candles.

        Args:
            dados: Dicionário com dados de análise.
            direcao: Direção do sinal.

        Returns:
            tuple: (stop_loss, take_profit).
        """
        try:
            # Garante que candles seja dict antes de acessar 'padroes'
            esperado = {"ALTA": "compra", "BAIXA": "venda"}.get(direcao)
            candles = dados.get("candles", {})
            padroes = candles.get("padroes", {}) if isinstance(candles, dict) else {}
            for padrao in padroes.values():
                if padrao.get("sinal") == esperado:
                    return padrao.get("stop_loss"), padrao.get("take_profit")
            return None, None
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair SL/TP: {e}")
            return None, None

    def _extrair_timestamp(self, dados: dict) -> float:
        """
        Extrai o timestamp da última candle.

        Args:
            dados: Dicionário com dados de análise.

        Returns:
            float: Timestamp ou None.
        """
        try:
            crus = dados.get("crus", [])
            if crus and isinstance(crus[-1], (list, tuple)) and len(crus[-1]) > 0:
                return float(crus[-1][0])
            return None
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao extrair timestamp: {e}")
            return None
