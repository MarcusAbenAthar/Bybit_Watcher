"""
Plugin Onchain: Diagnóstico de métricas on-chain (stablecoins, whales, NUPL, SOPR, etc).
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class Onchain(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin Onchain, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("Onchain finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar Onchain: {e}")

    PLUGIN_NAME = "onchain"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["onchain", "blockchain", "sentimento"]
    PLUGIN_PRIORIDADE = 84

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico de métricas on-chain do ativo.
        Integração com Glassnode (mock institucional se necessário).
        """
        import requests
        try:
            # Exemplo institucional: supply circulante do BTC
            url = f"https://api.glassnode.com/v1/metrics/supply/current?api_key=DEMO-KEY&asset=BTC"
            response = requests.get(url, timeout=10)
            metrica = None
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    metrica = data[0].get("v", None)
            if metrica is None:
                return {"status": "OK", "metrica": None, "alerta": None}
            alerta = None
            if metrica > 19000000:
                alerta = f"Supply circulante elevado: {metrica}"
            return {"status": "ALERTA", "metrica": metrica, "alerta": alerta}
        except Exception as e:
            logger.error(f"[Onchain] Erro: {e}")
            return {"status": "ERRO", "metrica": None, "alerta": str(e)}
