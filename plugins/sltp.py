# sltp.py
# Plugin SLTP

from typing import Dict, Any, Optional
from plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SLTP(Plugin):
    PLUGIN_NAME = "SLTP"
    PLUGIN_TYPE = "adicional"

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
        """
        Carrega os estilos de SL/TP da config ou define padrões com aviso.
        """
        estilos = config.get("sltp_estilos")
        if estilos and isinstance(estilos, dict):
            logger.info(f"Estilos SL/TP carregados da configuração.")
            return estilos

        logger.warning("Estilos SL/TP não encontrados na config. Usando padrão.")
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
            logger.error(f"Erro na simulação de cenários dinâmicos: {e}")
            return {}

    def _ajustar_por_performance(self) -> str:
        try:
            if not self._historico_resultados:
                return self._get_estilo_padrao()

            ultimos = self._historico_resultados[-5:]
            acertos = [r["resultado"] == "TP" for r in ultimos]
            erros = [r["resultado"] == "SL" for r in ultimos]

            if sum(acertos) >= 4 and "agressivo" in self._estilos_sltp:
                return "agressivo"
            if sum(erros) >= 3 and "conservador" in self._estilos_sltp:
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"Erro no ajuste por performance: {e}")
            return self._get_estilo_padrao()

    def _contexto_multitemporal(self, contexto: Dict[str, Any], direcao: str) -> str:
        try:
            tendencia_macro = contexto.get("tendencia_macro", "NEUTRO")
            if tendencia_macro != direcao and "conservador" in self._estilos_sltp:
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"Erro na análise de contexto multitemporal: {e}")
            return self._get_estilo_padrao()

    def _consolidar_com_indicadores(
        self, sl: float, tp: float, contexto: Dict[str, Any]
    ) -> Dict[str, float]:
        try:
            mm_barreira = contexto.get("ma_resistencia") or 0.0
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
            registro = {
                "direcao": sinal["direcao"],
                "sl": sinal["stop_loss"],
                "tp": sinal["take_profit"],
                "indicadores": sinal.get("indicadores_ativos", []),
                "resultado": resultado,
            }
            self._historico_resultados.append(registro)
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
            sinal = kwargs.get("sinal", {})

            cenarios = self._simular_cenarios(atr, candle_tamanho)
            estilo_contexto = self._contexto_multitemporal(contexto, direcao)
            estilo_performance = self._ajustar_por_performance()

            estilo_final = estilo_contexto
            if estilo_contexto != "conservador" and estilo_performance == "conservador":
                estilo_final = "conservador"
            elif estilo_performance in self._estilos_sltp:
                estilo_final = estilo_performance

            sltp_bruto = cenarios.get(
                estilo_final, cenarios.get(self._get_estilo_padrao())
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
            logger.error(f"Erro no SLTP: {e}", exc_info=True)
            return None
