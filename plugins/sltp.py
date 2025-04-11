"""Plugin SLTP inteligente com adaptação dinâmica baseada em contexto, performance e confiança."""

from typing import Dict, Any, Optional
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SLTP(Plugin):
    PLUGIN_NAME = "sltp"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["gerador", "sinal", "sltp"]
    PLUGIN_PRIORIDADE = 90

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._historico_resultados = []
        self._estilos_sltp = {}

    def inicializar(self, config: Dict[str, Any]) -> bool:
        if not super().inicializar(config):
            return False
        self._estilos_sltp = self._carregar_estilos(config)
        return True

    def _carregar_estilos(self, config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        estilos = config.get("sltp_estilos")
        if estilos and isinstance(estilos, dict):
            logger.info("Estilos SL/TP carregados da configuração.")
            return estilos

        logger.warning("Estilos SL/TP não encontrados. Usando valores padrão.")
        return {
            "conservador": {"sl_mult": 0.5, "tp_mult": 1.0},
            "moderado": {"sl_mult": 1.0, "tp_mult": 1.5},
            "agressivo": {"sl_mult": 1.5, "tp_mult": 3.0},
        }

    def _get_estilo_padrao(self) -> str:
        return self._config.get("sltp_estilo_padrao") or next(
            iter(self._estilos_sltp), "moderado"
        )

    def _simular_cenarios(
        self, atr: float, candle_tamanho: float
    ) -> Dict[str, Dict[str, float]]:
        try:
            return {
                estilo: {
                    "sl": round(atr * params.get("sl_mult", 1.0), 4),
                    "tp": round(atr * params.get("tp_mult", 1.5), 4),
                }
                for estilo, params in self._estilos_sltp.items()
            }
        except Exception as e:
            logger.error(f"Erro na simulação de SL/TP: {e}")
            return {}

    def _ajustar_por_performance(self) -> str:
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
            logger.error(f"Erro na avaliação de performance: {e}")
            return self._get_estilo_padrao()

    def _contexto_multitemporal(
        self, contexto: Dict[str, Any], direcao: str, forca: str
    ) -> str:
        try:
            tendencia_macro = contexto.get("tendencia_macro", "NEUTRO")
            if tendencia_macro != direcao or forca == "LATERAL":
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"Erro na avaliação de contexto: {e}")
            return self._get_estilo_padrao()

    def _consolidar_com_indicadores(
        self, sl: float, tp: float, contexto: Dict[str, Any]
    ) -> Dict[str, float]:
        try:
            mm_barreira = contexto.get("ma_resistencia", 0.0)
            sl_ajustado = max(sl, mm_barreira * 0.05)
            return {
                "stop_loss": round(sl_ajustado, 2),
                "take_profit": round(tp, 2),
            }
        except Exception as e:
            logger.error(f"Erro na consolidação com indicadores: {e}")
            return {"stop_loss": sl, "take_profit": tp}

    def _registrar_resultado(self, sinal: Dict[str, Any], resultado: str):
        try:
            self._historico_resultados.append(
                {
                    "direcao": sinal.get("direcao"),
                    "sl": sinal.get("stop_loss"),
                    "tp": sinal.get("take_profit"),
                    "indicadores": sinal.get("indicadores_ativos", []),
                    "resultado": resultado,
                }
            )
        except Exception as e:
            logger.error(f"Erro ao registrar resultado do sinal: {e}")

    def executar(self, **kwargs) -> Optional[Dict[str, float]]:
        if not self.inicializado:
            logger.error(f"Plugin {self.nome} não inicializado")
            return None

        try:
            contexto = kwargs.get("contexto", {})
            atr = kwargs.get("atr")
            candle_tamanho = kwargs.get("candle_tamanho")
            direcao = kwargs.get("direcao")
            forca = kwargs.get("forca", "FRACA")
            sinal = kwargs.get("sinal", {})

            cenarios = self._simular_cenarios(atr, candle_tamanho)
            estilo_contexto = self._contexto_multitemporal(contexto, direcao, forca)
            estilo_performance = self._ajustar_por_performance()

            estilo_final = "conservador"
            if estilo_contexto != "conservador" and estilo_performance != "conservador":
                estilo_final = estilo_performance

            sltp_bruto = cenarios.get(estilo_final) or cenarios.get(
                self._get_estilo_padrao()
            )
            sltp_final = self._consolidar_com_indicadores(
                sltp_bruto["sl"], sltp_bruto["tp"], contexto
            )

            self._registrar_resultado(
                {
                    **sinal,
                    **sltp_final,
                    "indicadores": contexto.get("indicadores_ativos", []),
                },
                resultado=sinal.get("resultado", "nenhum"),
            )

            logger.info(f"SL/TP gerados ({estilo_final}): {sltp_final}")
            return sltp_final
        except Exception as e:
            logger.error(f"Erro ao executar SLTP: {e}", exc_info=True)
            return None
