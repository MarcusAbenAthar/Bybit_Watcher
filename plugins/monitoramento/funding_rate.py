"""
Plugin FundingRate: Consulta e diagnostica o funding rate de derivativos para auxiliar decisões estratégicas.
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class FundingRate(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin FundingRate, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("FundingRate finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar FundingRate: {e}")

    PLUGIN_NAME = "funding_rate"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["funding", "derivativos", "sentimento"]
    PLUGIN_PRIORIDADE = 80

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico do funding rate para o par informado.
        """
        import requests
        try:
            url = f"https://api.bybit.com/v5/market/funding-rate?symbol={symbol}"
            response = requests.get(url, timeout=10)
            funding = None
            if response.status_code == 200:
                data = response.json()
                rows = data.get("result", {}).get("list", [])
                if rows:
                    funding = float(rows[0].get("fundingRate", 0))
            if funding is None:
                return {"status": "OK", "funding_rate": None, "alerta": None}
            alerta = None
            if abs(funding) > 0.01:
                alerta = f"Funding rate extremo: {funding:.4f}"
            return {"status": "ALERTA", "funding_rate": funding, "alerta": alerta}
        except Exception as e:
            logger.error(f"[FundingRate] Erro: {e}")
            return {"status": "ERRO", "funding_rate": None, "alerta": str(e)}
