"""
Plugin MLPreditor: Previsão de curto prazo usando machine learning.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class MLPreditor(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin MLPreditor, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("MLPreditor finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar MLPreditor: {e}")

    PLUGIN_NAME = "ml_preditor"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["ml", "ia", "previsao"]
    PLUGIN_PRIORIDADE = 89

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, candles=None) -> dict:
        """
        Diagnóstico preditivo usando ML (regressão linear sklearn).
        Retorna status, previsão e alerta estratégico.
        """
        try:
            from sklearn.linear_model import LinearRegression
            import numpy as np
            if candles is None or len(candles) < 30:
                logger.warning("Candles insuficientes para predição.")
                return {"status": "DADOS_INCOMPLETOS", "previsao": None, "alerta": "Poucos candles"}
            closes = np.array([c[4] for c in candles]).reshape(-1, 1)
            X = np.arange(len(closes)).reshape(-1, 1)
            model = LinearRegression().fit(X, closes)
            previsao = float(model.predict([[len(closes)]])[0])
            alerta = None
            if abs((previsao - closes[-1][0]) / closes[-1][0]) > 0.05:
                alerta = f"Predição de movimento relevante: {previsao:.4f}"
            return {"status": "ALERTA", "previsao": previsao, "alerta": alerta}
        except Exception as e:
            logger.error(f"[MLPreditor] Erro: {e}")
            return {"status": "ERRO", "previsao": None, "alerta": str(e)}
