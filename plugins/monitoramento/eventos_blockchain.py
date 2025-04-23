"""
Plugin EventosBlockchain: Sinaliza eventos críticos do universo cripto (halving, unlocks, vencimentos, upgrades).
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class EventosBlockchain(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin EventosBlockchain, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("EventosBlockchain finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar EventosBlockchain: {e}")

    PLUGIN_NAME = "eventos_blockchain"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["eventos", "blockchain", "macro"]
    PLUGIN_PRIORIDADE = 83

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico de eventos relevantes na blockchain para o ativo.
        Integra CoinMarketCal para eventos futuros relevantes.
        """
        import requests
        try:
            url = f"https://developers.coinmarketcal.com/v1/events?coins={symbol[:3].lower()}"
            headers = {"Accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            eventos = []
            if response.status_code == 200:
                data = response.json()
                for ev in data.get("body", []):
                    eventos.append({
                        "title": ev.get("title", ""),
                        "date": ev.get("date_event", ""),
                        "category": ev.get("categories", [{}])[0].get("name", "")
                    })
            if not eventos:
                return {"status": "OK", "eventos": [], "alerta": None}
            alerta = f"{len(eventos)} eventos relevantes detectados!"
            return {"status": "ALERTA", "eventos": eventos, "alerta": alerta}
        except Exception as e:
            logger.error(f"[EventosBlockchain] Erro: {e}")
            return {"status": "ERRO", "eventos": [], "alerta": str(e)}
