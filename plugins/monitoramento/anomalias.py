"""
Plugin Anomalias: Detecção de outliers e anomalias em preço, volume e volatilidade.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)
# Todos os logs deste plugin são exclusivos para monitoramento.

class Anomalias(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin Anomalias, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("Anomalias finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar Anomalias: {e}")

    PLUGIN_NAME = "anomalias"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["anomalia", "outlier", "detecção"]
    PLUGIN_PRIORIDADE = 87

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, candles=None) -> dict:
        """
        Diagnóstico de anomalias em candles (preço, volume, volatilidade).
        Retorna status, lista de anomalias e alerta estratégico.
        """
        import numpy as np
        try:
            if candles is None or len(candles) < 30:
                logger.warning("Candles insuficientes para análise de anomalias.")
                return {"status": "DADOS_INCOMPLETOS", "anomalias": [], "alerta": "Poucos candles"}
            closes = np.array([c[4] for c in candles])  # Supondo OHLCV
            volumes = np.array([c[5] for c in candles])
            volatilidade = closes.std() / closes.mean() if closes.mean() else 0
            z_close = (closes - closes.mean()) / closes.std() if closes.std() else closes*0
            z_vol = (volumes - volumes.mean()) / volumes.std() if volumes.std() else volumes*0
            anomalias = []
            for i, (z_c, z_v) in enumerate(zip(z_close, z_vol)):
                if abs(z_c) > 3:
                    anomalias.append({"tipo": "preco", "indice": i, "zscore": float(z_c)})
                if abs(z_v) > 3:
                    anomalias.append({"tipo": "volume", "indice": i, "zscore": float(z_v)})
            alerta = None
            if anomalias:
                alerta = f"{len(anomalias)} anomalias detectadas!"
                return {"status": "ALERTA", "anomalias": anomalias, "alerta": alerta}
            return {"status": "OK", "anomalias": [], "alerta": None}
        except Exception as e:
            logger.error(f"[Anomalias] Erro: {e}")
            return {"status": "ERRO", "anomalias": [], "alerta": str(e)}

