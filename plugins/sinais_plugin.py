"""
Plugin para consolidação de dados de análise e geração do sinal final
com SL/TP, confiança e alavancagem.
"""

from utils.logging_config import get_logger
from plugins.plugin import Plugin
import logging

logger = get_logger(__name__)
logger_sinais = logging.getLogger("sinais")


class SinaisPlugin(Plugin):
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
            logger.info(f"[{self.nome}] Sinais consolidados: {sinais}")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na execução: {e}", exc_info=True)
            dados_completos["sinais"] = resultado_padrao["sinais"]
            return True

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
            direcao = analise.get("direcao", "LATERAL")
            forca = analise.get("forca", "FRACA")
            confianca_base = analise.get("confianca", 0.0)

            confianca = self._calcular_confianca(dados, direcao, confianca_base)
            alavancagem = self._calcular_alavancagem(dados, direcao, confianca)
            stop_loss, take_profit = self._extrair_sl_tp(dados, direcao)
            timestamp = self._extrair_timestamp(dados)

            sinal = {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "alavancagem": alavancagem,
                "timestamp": timestamp,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

            logger_sinais.info(
                f"[{symbol} - {timeframe}] DIREÇÃO: {direcao} | FORÇA: {forca} | "
                f"CONFIANÇA: {confianca:.2f} | ALAVANCAGEM: {alavancagem:.2f}x | "
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

        Args:
            dados: Dicionário com dados de análise.
            direcao: Direção do sinal principal.
            base: Confiança base de analise_mercado.

        Returns:
            float: Confiança consolidada (0.0 a 1.0).
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
            if self._calculo_risco and dados.get("calculo_risco"):
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
                min(max(resultado, self._confianca_min), self._confianca_max), 2
            )
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
            esperado = {"ALTA": "compra", "BAIXA": "venda"}.get(direcao)
            padroes = dados.get("candles", {}).get("padroes", {})
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
