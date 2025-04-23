"""
Plugin OpenInterest: Consulta e diagnostica o open interest de derivativos.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class OpenInterest(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin OpenInterest, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("OpenInterest finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar OpenInterest: {e}")

    PLUGIN_NAME = "open_interest"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["open_interest", "derivativos", "sentimento"]
    PLUGIN_PRIORIDADE = 81

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico de open interest do ativo.
        Consulta Bybit API pública ou retorna mock institucional.
        """
        import requests
        try:
            url = f"https://api.bybit.com/v5/market/open-interest?symbol={symbol}&interval=1h"
            response = requests.get(url, timeout=10)
            oi = None
            if response.status_code == 200:
                data = response.json()
                rows = data.get("result", {}).get("list", [])
                if rows:
                    oi = float(rows[-1].get("openInterest", 0))
            if oi is None:
                return {"status": "OK", "open_interest": None, "alerta": None}
            alerta = None
            if oi > 1000000:
                alerta = f"Open interest elevado: {oi}"
            return {"status": "ALERTA", "open_interest": oi, "alerta": alerta}
        except Exception as e:
            logger.error(f"[OpenInterest] Erro: {e}")
            return {"status": "ERRO", "open_interest": None, "alerta": str(e)}
