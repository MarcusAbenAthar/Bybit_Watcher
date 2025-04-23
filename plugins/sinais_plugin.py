"""
Plugin para consolidação de dados de análise e geração do sinal final
com SL/TP, confiança e alavancagem.
"""

from utils.logging_config import get_logger
from plugins.plugin import Plugin
import logging

logger = get_logger(__name__)
logger_sinais = logging.getLogger("sinais")


class SinaisPlugin(...):
    def finalizar(self):
        """
        Finaliza o plugin SinaisPlugin, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("SinaisPlugin finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar SinaisPlugin: {e}")

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

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin SinaisPlugin.
        """
        return [
            "price_action",
            "medias_moveis",
            "indicadores_tendencia",
            "indicadores_osciladores",
            "indicadores_volatilidade",
            "indicadores_volume",
        ]

    def consolidar_sinais_multi_timeframe(self, sinais_timeframes: dict, symbol: str, config: dict) -> dict:
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
                forca = 1 if str(sinal.get("forca", "FRACA")).upper() == "FORTE" else (0.5 if str(sinal.get("forca", "FRACA")).upper() == "MEDIA" or str(sinal.get("forca", "FRACA")).upper() == "MÉDIA" else 0)
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

    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["consolidacao", "sinal", "output"]
    PLUGIN_PRIORIDADE = 99

    def __init__(self, calculo_alavancagem=None, calculo_risco=None, **kwargs):
        """
        Inicializa o plugin SinaisPlugin com dependências injetadas.

        Args:
            calculo_alavancagem: Instância de CalculoAlavancagem.
            calculo_risco: Instância de CalculoRisco.
            **kwargs: Outras dependências.
        """
        super().__init__(**kwargs)
        self._calculo_alavancagem = calculo_alavancagem
        self._calculo_risco = calculo_risco
        self._confianca_pesos = {
            "analise_mercado": 0.4,
            "calculo_risco": 0.3,
            "outros": 0.3,
        }
        self._confianca_min = 0.0
        self._confianca_max = 1.0

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

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa a consolidação de sinais e armazena o resultado.

        Args:
            symbol (str): Símbolo do par.
            timeframe (str): Timeframe.
            dados_completos (dict): Dados de análise.
            config (dict, optional): Configurações.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")
        dados_completos = kwargs.get("dados_completos", {})
        config = kwargs.get("config", self._config)

        resultado_padrao = {
            "sinais": {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
                "stop_loss": None,
                "take_profit": None,
            }
        }

        if not isinstance(dados_completos, dict):
            logger.error(
                f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
            )
            dados_completos["sinais"] = resultado_padrao["sinais"]
            return True

        if not all([symbol, timeframe]):
            logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
            dados_completos["sinais"] = resultado_padrao["sinais"]
            return True

        if not dados_completos.get("analise_mercado"):
            logger.error(f"[{self.nome}] analise_mercado ausente em dados_completos")
            dados_completos["sinais"] = resultado_padrao["sinais"]
            return True

        try:
            logger.info(f"[{self.nome}] Processando {symbol} - {timeframe}")
            sinais = self._gerar_sinal(dados_completos, symbol, timeframe)
            dados_completos["sinais"] = sinais
            logger.info(f"[{self.nome}] Sinais consolidados [{symbol}]: {sinais}")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na execução: {e}", exc_info=True)
            dados_completos["sinais"] = resultado_padrao["sinais"]
            return True

    def _volume_acima_media(self, candles: list, n: int = 20) -> bool:
        """
        Retorna True se o volume do candle mais recente estiver acima da média dos últimos n candles.
        """
        try:
            if not candles or len(candles) < n + 1:
                return False
            volumes = [float(c[5]) for c in candles[-(n+1):]]
            return volumes[-1] > (sum(volumes[:-1]) / n)
        except Exception as e:
            logger.error(f"[sinais_plugin] Erro ao validar volume: {e}")
            return False

    def _preco_acima_media(self, candles: list, periodo: int = 20) -> bool:
        """
        Retorna True se o preço de fechamento atual está acima da média móvel simples dos últimos 'periodo' candles.
        """
        try:
            if not candles or len(candles) < periodo:
                return False
            closes = [float(c[4]) for c in candles[-periodo:]]
            return closes[-1] > (sum(closes[:-1]) / (periodo-1))
        except Exception as e:
            logger.error(f"[sinais_plugin] Erro ao validar média móvel: {e}")
            return False

    def _proximo_resistencia(self, close: float, resistencias: list, margem: float = 0.001) -> bool:
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

            confianca = self._calcular_confianca(dados, direcao_original, confianca_base)
            confianca_pct = round(confianca * 100, 2)
            alavancagem = self._calcular_alavancagem(dados, direcao, confianca)
            stop_loss, take_profit = self._extrair_sl_tp(dados, direcao)
            timestamp = self._extrair_timestamp(dados)

            # Filtro de confiança mínima
            confianca_min = self._confianca_min if hasattr(self, '_confianca_min') else 0.6
            if confianca < confianca_min:
                logger.info(f"[sinais_plugin] Sinal descartado por confiança baixa: {confianca:.2f}")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": timestamp,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            # Filtro de volume relativo
            candles = dados.get("crus", [])
            if not self._volume_acima_media(candles, n=20):
                logger.info(f"[sinais_plugin] Sinal descartado por volume abaixo da média.")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": timestamp,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            # Validação de contexto: preço acima da média móvel
            if direcao == "LONG" and not self._preco_acima_media(candles, periodo=20):
                logger.info(f"[sinais_plugin] Sinal LONG descartado: preço não está acima da média móvel.")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": timestamp,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            # Validação de resistência (exemplo usando candles, pode ser extendido)
            close = float(candles[-1][4]) if candles else 0.0
            resistencias = []
            if "pivots" in dados and isinstance(dados["pivots"], dict):
                resistencias = dados["pivots"].get("resistencias", [])
            if self._proximo_resistencia(close, resistencias, margem=0.0015):
                logger.info(f"[sinais_plugin] Sinal descartado: preço próximo de resistência relevante.")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": timestamp,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

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
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
                "stop_loss": None,
                "take_profit": None,
            }

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
                confiancas.append((confianca_analise, self._confianca_pesos.get("analise_mercado", 0.4)))

            # Peso para calculo_risco
            if self._calculo_risco and dados.get("calculo_risco"):
                confianca_risco = dados["calculo_risco"].get("confianca", 0.0)
                dir_risco = dados["calculo_risco"].get("direcao", "LATERAL")
                if confianca_risco > 0:
                    confiancas.append((confianca_risco, self._confianca_pesos.get("calculo_risco", 0.3)))
                    if dir_risco == direcao:
                        ajuste += 0.1
                    elif dir_risco != "LATERAL":
                        ajuste -= 0.1

            # Outros plugins
            for chave, info in dados.items():
                if chave not in ["analise_mercado", "calculo_risco", "crus", "sinais"] and isinstance(info, dict):
                    c = info.get("confianca", 0.0)
                    if c > 0:
                        confiancas.append((c, self._confianca_pesos.get("outros", 0.3) / max(1, len(dados) - 3)))
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
            return round(min(max(resultado, self._confianca_min), self._confianca_max), 4)  # Mais precisão interna
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao calcular confiança: {e}", exc_info=True)
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
        if not self._calculo_alavancagem:
            logger.warning(
                f"[{self.nome}] Plugin de cálculo de alavancagem não disponível"
            )
            return 0.0

        try:
            return self._calculo_alavancagem.calcular_alavancagem(
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
