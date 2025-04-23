"""
Plugin Orderbook: Diagnóstico de clusters de ordens e anomalias de liquidez.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class Orderbook(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin Orderbook, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("Orderbook finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar Orderbook: {e}")

    PLUGIN_NAME = "orderbook"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["orderbook", "profundidade", "liquidez", "sentimento"]
    PLUGIN_PRIORIDADE = 82

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico do orderbook do ativo.
        Consulta Bybit API pública ou retorna mock institucional.
        """
        import requests
        try:
            url = f"https://api.bybit.com/v5/market/orderbook?symbol={symbol}&category=linear"
            response = requests.get(url, timeout=10)
            clusters = []
            if response.status_code == 200:
                data = response.json()
                bids = data.get("result", {}).get("b", [])
                asks = data.get("result", {}).get("a", [])
                # Exemplo: clusters de bids/asks acima de um certo volume
                for book, side in [(bids, "bid"), (asks, "ask")]:
                    for price, qty in book:
                        if float(qty) > 100:
                            clusters.append({"side": side, "price": float(price), "qty": float(qty)})
            if not clusters:
                logger.info("[Orderbook] Sem clusters relevantes detectados.")
                return {"status": "OK", "clusters": [], "alerta": None}
            alerta = f"{len(clusters)} clusters de liquidez detectados!"
            return {"status": "ALERTA", "clusters": clusters, "alerta": alerta}
        except Exception as e:
            logger.error(f"[Orderbook] Erro: {e}")
            return {"status": "ERRO", "clusters": [], "alerta": str(e)}
