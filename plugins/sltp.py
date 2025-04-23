"""
Plugin SLTP inteligente com adaptação dinâmica baseada em contexto, performance e confiança.
"""

from typing import Dict, Any, Optional
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SLTP(...):
    def finalizar(self):
        """
        Finaliza o plugin SLTP, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("SLTP finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar SLTP: {e}")

class SLTP(Plugin):
    """
    Plugin para cálculo inteligente de Stop Loss (SL) e Take Profit (TP), com lógica adaptativa.
    - Responsabilidade única: cálculo de SL/TP.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "sltp"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sltp", "gerenciamento", "risco"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin SLTP.
        """
        return ["calculo_risco", "calculo_alavancagem"]

    PLUGIN_NAME = "sltp"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["gerador", "sinal", "sltp"]
    PLUGIN_PRIORIDADE = 90

    def __init__(self, **kwargs):
        """
        Inicializa o plugin SLTP.

        Args:
            **kwargs: Dependências injetadas.
        """
        super().__init__(**kwargs)
        self._historico_resultados = []
        self._estilos_sltp = {}
        self._max_historico = 100  # Limite para histórico em memória

    def inicializar(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa o plugin com configurações.

        Args:
            config: Dicionário com configurações.

        Returns:
            bool: True se inicializado, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            self._estilos_sltp = self._carregar_estilos(config)
            if not self._estilos_sltp:
                logger.error(f"[{self.nome}] Nenhum estilo SL/TP válido carregado")
                return False

            logger.info(
                f"[{self.nome}] Inicializado com estilos: {list(self._estilos_sltp.keys())}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def _carregar_estilos(self, config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Carrega estilos SL/TP da configuração.

        Args:
            config: Dicionário com configurações.

        Returns:
            dict: Estilos SL/TP válidos.
        """
        try:
            estilos = config.get("sltp_estilos", {})
            estilos_padrao = {
                "conservador": {"sl_mult": 0.5, "tp_mult": 1.0},
                "moderado": {"sl_mult": 1.0, "tp_mult": 1.5},
                "agressivo": {"sl_mult": 1.5, "tp_mult": 3.0},
            }

            if not isinstance(estilos, dict) or not estilos:
                logger.warning(
                    f"[{self.nome}] Estilos SL/TP não encontrados. Usando padrão."
                )
                return estilos_padrao

            estilos_validados = {}
            for nome, params in estilos.items():
                if not isinstance(params, dict):
                    logger.warning(f"[{self.nome}] Estilo {nome} inválido: {params}")
                    continue
                sl_mult = params.get("sl_mult")
                tp_mult = params.get("tp_mult")
                if (
                    isinstance(sl_mult, (int, float))
                    and isinstance(tp_mult, (int, float))
                    and sl_mult > 0
                    and tp_mult > 0
                ):
                    estilos_validados[nome] = {"sl_mult": sl_mult, "tp_mult": tp_mult}
                else:
                    logger.warning(
                        f"[{self.nome}] Parâmetros inválidos para {nome}: {params}"
                    )
            if not estilos_validados:
                logger.warning(f"[{self.nome}] Nenhum estilo válido. Usando padrão.")
                return estilos_padrao

            logger.info(
                f"[{self.nome}] Estilos SL/TP carregados: {list(estilos_validados.keys())}"
            )
            return estilos_validados
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao carregar estilos: {e}")
            return {"moderado": {"sl_mult": 1.0, "tp_mult": 1.5}}

    def _get_estilo_padrao(self) -> str:
        """
        Retorna o estilo padrão.

        Returns:
            str: Nome do estilo padrão.
        """
        try:
            estilo = self._config.get("sltp_estilo_padrao", "moderado")
            if estilo in self._estilos_sltp:
                return estilo
            logger.warning(
                f"[{self.nome}] Estilo padrão {estilo} não encontrado. Usando primeiro disponível."
            )
            return next(iter(self._estilos_sltp), "moderado")
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao obter estilo padrão: {e}")
            return "moderado"

    def _simular_cenarios(
        self, atr: float, candle_tamanho: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Simula cenários SL/TP para cada estilo.

        Args:
            atr: Valor do ATR.
            candle_tamanho: Tamanho da candle.

        Returns:
            dict: Cenários SL/TP por estilo.
        """
        try:
            if not isinstance(atr, (int, float)) or atr <= 0:
                logger.error(f"[{self.nome}] ATR inválido: {atr}")
                return {}
            return {
                estilo: {
                    "sl": round(atr * params.get("sl_mult", 1.0), 4),
                    "tp": round(atr * params.get("tp_mult", 1.5), 4),
                }
                for estilo, params in self._estilos_sltp.items()
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na simulação de SL/TP: {e}")
            return {}

    def _ajustar_por_performance(self) -> str:
        """
        Ajusta o estilo com base na performance histórica.

        Returns:
            str: Estilo ajustado.
        """
        try:
            if not self._historico_resultados:
                return self._get_estilo_padrao()

            ultimos = self._historico_resultados[-5:]
            acertos = sum(1 for r in ultimos if r["resultado"] == "TP")
            erros = sum(1 for r in ultimos if r["resultado"] == "SL")

            if acertos >= 4 and "agressivo" in self._estilos_sltp:
                return "agressivo"
            if erros >= 3 and "conservador" in self._estilos_sltp:
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na avaliação de performance: {e}")
            return self._get_estilo_padrao()

    def _contexto_multitemporal(
        self, contexto: Dict[str, Any], direcao: str, forca: str
    ) -> str:
        """
        Avalia o contexto multitemporal para selecionar estilo.

        Args:
            contexto: Dados de contexto.
            direcao: Direção do sinal.
            forca: Força do sinal.

        Returns:
            str: Estilo selecionado.
        """
        try:
            tendencia_macro = contexto.get("tendencia_macro", "LATERAL")
            # Compatibilidade com "NEUTRO" da versão original
            if tendencia_macro == "NEUTRO":
                tendencia_macro = "LATERAL"
            if tendencia_macro != direcao or forca == "LATERAL":
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na avaliação de contexto: {e}")
            return self._get_estilo_padrao()

    def _consolidar_com_indicadores(
        self,
        sl: float,
        tp: float,
        contexto: Dict[str, Any],
        direcao: str,
        preco_atual: float,
    ) -> Dict[str, float]:
        """
        Ajusta SL/TP com base em indicadores e direção.

        Args:
            sl: Stop-loss bruto.
            tp: Take-profit bruto.
            contexto: Dados de contexto.
            direcao: Direção do sinal.
            preco_atual: Preço atual do ativo.

        Returns:
            dict: SL/TP ajustados.
        """
        try:
            mm_barreira = contexto.get("ma_resistencia", 0.0)
            sl_ajustado = max(sl, mm_barreira * 0.05) if mm_barreira > 0 else sl

            # Ajustar SL/TP com base na direção
            if direcao == "ALTA":
                stop_loss = preco_atual - sl_ajustado
                take_profit = preco_atual + tp
            elif direcao == "BAIXA":
                stop_loss = preco_atual + sl_ajustado
                take_profit = preco_atual - tp
            else:
                stop_loss = preco_atual - sl_ajustado  # Padrão conservador
                take_profit = preco_atual + tp

            return {
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na consolidação com indicadores: {e}")
            return {
                "stop_loss": round(preco_atual - sl, 2),
                "take_profit": round(preco_atual + tp, 2),
            }

    def _registrar_resultado(self, sinal: Dict[str, Any], resultado: str):
        """
        Registra o resultado do sinal no histórico.

        Args:
            sinal: Dados do sinal.
            resultado: Resultado ("TP", "SL", "nenhum").
        """
        try:
            registro = {
                "direcao": sinal.get("direcao"),
                "sl": sinal.get("stop_loss"),
                "tp": sinal.get("take_profit"),
                "indicadores": sinal.get("indicadores_ativos", []),
                "resultado": resultado,
            }
            self._historico_resultados.append(registro)
            if len(self._historico_resultados) > self._max_historico:
                self._historico_resultados.pop(0)
            # TODO: Integrar com banco_dados.py quando implementado
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao registrar resultado: {e}")

    def executar(self, **kwargs) -> bool:
        """
        Executa a geração de SL/TP e atualiza dados_completos.

        Args:
            **kwargs: Inclui contexto, atr, candle_tamanho, direcao, forca, sinal, dados_completos.

        Returns:
            bool: True (mesmo em erro, para não interromper o pipeline).
        """
        if not self.inicializado:
            logger.error(f"[{self.nome}] Não inicializado")
            dados_completos = kwargs.get("dados_completos", {})
            if isinstance(dados_completos, dict):
                dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
            return True

        try:
            dados_completos = kwargs.get("dados_completos", {})
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
                return True

            contexto = kwargs.get("contexto", {})
            atr = kwargs.get("atr", 0.0)
            candle_tamanho = kwargs.get("candle_tamanho", 0.0)
            direcao = kwargs.get("direcao", "LATERAL")
            forca = kwargs.get("forca", "FRACA")
            sinal = kwargs.get("sinal", {})
            preco_atual = (
                dados_completos.get("crus", [[]])[-1][4]
                if dados_completos.get("crus")
                else 0.0
            )

            if not isinstance(atr, (int, float)) or atr <= 0:
                logger.error(f"[{self.nome}] ATR inválido: {atr}")
                dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
                return True
            if not isinstance(candle_tamanho, (int, float)) or candle_tamanho <= 0:
                logger.warning(
                    f"[{self.nome}] candle_tamanho inválido: {candle_tamanho}. Ignorando."
                )
                candle_tamanho = atr  # Fallback
            if direcao not in ["ALTA", "BAIXA", "LATERAL", "NEUTRO"]:
                logger.error(f"[{self.nome}] Direção inválida: {direcao}")
                dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
                return True
            if preco_atual <= 0:
                logger.error(f"[{self.nome}] Preço atual inválido: {preco_atual}")
                dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
                return True

            cenarios = self._simular_cenarios(atr, candle_tamanho)
            if not cenarios:
                logger.error(f"[{self.nome}] Nenhum cenário SL/TP gerado")
                dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
                return True

            estilo_contexto = self._contexto_multitemporal(contexto, direcao, forca)
            estilo_performance = self._ajustar_por_performance()

            estilo_final = (
                "conservador"
                if "conservador" in self._estilos_sltp
                else self._get_estilo_padrao()
            )
            if estilo_contexto != "conservador" and estilo_performance != "conservador":
                estilo_final = estilo_performance

            sltp_bruto = cenarios.get(estilo_final) or cenarios.get(
                self._get_estilo_padrao()
            )
            sltp_final = self._consolidar_com_indicadores(
                sltp_bruto["sl"], sltp_bruto["tp"], contexto, direcao, preco_atual
            )

            self._registrar_resultado(
                {
                    **sinal,
                    **sltp_final,
                    "direcao": direcao,
                    "indicadores_ativos": contexto.get("indicadores_ativos", []),
                },
                resultado=sinal.get("resultado", "nenhum"),
            )

            dados_completos["sltp"] = sltp_final
            logger.info(f"[{self.nome}] SL/TP gerados ({estilo_final}): {sltp_final}")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            dados_completos["sltp"] = {"stop_loss": None, "take_profit": None}
            return True
