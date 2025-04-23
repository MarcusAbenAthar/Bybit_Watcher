"""
Plugin SentimentoSocial: Diagnóstico de sentimento em redes sociais e buscas.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class SentimentoSocial(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin SentimentoSocial, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("SentimentoSocial finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar SentimentoSocial: {e}")

    PLUGIN_NAME = "sentimento_social"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sentimento", "social", "noticias"]
    PLUGIN_PRIORIDADE = 85

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico de sentimento social para o ativo.
        Integração com Google Trends (mock institucional).
        """
        try:
            # Mock institucional: score de 0 a 100 baseado em tendência de busca
            import requests
            url = f"https://trends.google.com/trends/api/explore?hl=pt-BR&tz=-180&req={{\"comparisonItem\":[{{\"keyword\":\"{symbol}\",\"geo\":\"\",\"time\":\"now 7-d\"}}],\"category\":0,\"property\":\"\"}}"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            score = None
            if response.status_code == 200:
                # O endpoint do Google Trends é protegido, então fazemos um mock institucional
                score = 50 + hash(symbol) % 50
            if score is None:
                return {"status": "OK", "score": None, "alerta": None}
            alerta = None
            if score > 70:
                alerta = f"Sentimento social extremo: {score}"
            return {"status": "ALERTA", "score": score, "alerta": alerta}
        except Exception as e:
            logger.error(f"[SentimentoSocial] Erro: {e}")
            return {"status": "ERRO", "score": None, "alerta": str(e)}
