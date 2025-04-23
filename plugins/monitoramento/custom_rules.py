"""
Plugin CustomRules: Permite definição de regras customizadas pelo usuário para alertas e diagnóstico.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)
# Todos os logs deste plugin são exclusivos para monitoramento.

class CustomRules(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin CustomRules, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("CustomRules finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar CustomRules: {e}")

    PLUGIN_NAME = "custom_rules"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["custom", "usuario", "regra"]
    PLUGIN_PRIORIDADE = 90

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, dados=None) -> dict:
        """
        Diagnóstico baseado em regras customizadas do usuário.
        Retorna status, resultado e alerta estratégico.
        """
        try:
            # Exemplo: regra customizada
            alerta = None
            if self.config.get("regra_exemplo", False):
                alerta = "Regra customizada disparada!"
            return {"status": "OK", "alerta": alerta}
        except Exception as e:
            logger.error(f"[CustomRules] Erro: {e}")
            return {"status": "ERRO", "alerta": str(e)}
