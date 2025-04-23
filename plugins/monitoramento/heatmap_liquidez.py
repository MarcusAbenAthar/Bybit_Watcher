"""
Plugin HeatmapLiquidez: Sinaliza zonas de liquidação e liquidez relevante.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class HeatmapLiquidez(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin HeatmapLiquidez, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("HeatmapLiquidez finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar HeatmapLiquidez: {e}")

    PLUGIN_NAME = "heatmap_liquidez"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["heatmap", "liquidez", "liquidacao"]
    PLUGIN_PRIORIDADE = 88

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico de heatmap de liquidez do ativo.
        Integração com Coinglass (mock institucional se necessário).
        """
        import requests
        try:
            url = f"https://open-api.coinglass.com/public/v2/liquidation?symbol={symbol}"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            zonas = []
            if response.status_code == 200:
                data = response.json()
                for zona in data.get("data", []):
                    zonas.append({
                        "price": zona.get("price"),
                        "volume": zona.get("volume"),
                        "side": zona.get("side")
                    })
            if not zonas:
                return {"status": "OK", "zonas": [], "alerta": None}
            alerta = f"{len(zonas)} zonas de liquidez detectadas!"
            return {"status": "ALERTA", "zonas": zonas, "alerta": alerta}
        except Exception as e:
            logger.error(f"[HeatmapLiquidez] Erro: {e}")
            return {"status": "ERRO", "zonas": [], "alerta": str(e)}
