"""
Plugin Correlatos: Diagnóstico de correlação com ativos tradicionais (S&P500, DXY, ouro).
Responsabilidade única. Modular, testável, documentado.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__, monitoramento=True)

class Correlatos(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin Correlatos, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("Correlatos finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar Correlatos: {e}")

    PLUGIN_NAME = "correlatos"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["correlacao", "macro", "tradfi"]
    PLUGIN_PRIORIDADE = 86

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', {})

    def diagnostico(self, symbol="BTCUSDT") -> dict:
        """
        Diagnóstico de correlação real com ativos tradicionais (S&P500, DXY, ouro).
        Retorna status, valores de correlação e alerta estratégico.
        """
        import yfinance as yf
        import numpy as np
        try:
            ativos_tradfi = {
                "sp500": "^GSPC",
                "dxy": "DX-Y.NYB",
                "gold": "GC=F",
            }
            # Baixa dados históricos (últimos 90 dias)
            dados_cripto = yf.download(symbol, period="90d", interval="1d")
            correlacoes = {}
            if dados_cripto.empty:
                logger.warning("Sem dados históricos para o ativo cripto.")
                return {"status": "DADOS_INCOMPLETOS", "correlacoes": {}, "alerta": "Sem dados do ativo cripto"}
            retornos_cripto = dados_cripto["Close"].pct_change().dropna()
            for nome, ticker in ativos_tradfi.items():
                dados_trad = yf.download(ticker, period="90d", interval="1d")
                if dados_trad.empty:
                    correlacoes[nome] = None
                    continue
                retornos_trad = dados_trad["Close"].pct_change().dropna()
                # Alinha datas
                comuns = retornos_cripto.index.intersection(retornos_trad.index)
                if len(comuns) < 30:
                    correlacoes[nome] = None
                    continue
                corr = np.corrcoef(retornos_cripto.loc[comuns], retornos_trad.loc[comuns])[0, 1]
                correlacoes[nome] = float(corr)
            alerta = None
            if correlacoes.get("sp500") and correlacoes["sp500"] > 0.7:
                alerta = "Mercado cripto altamente correlacionado com S&P500: risco de contágio!"
            return {"status": "OK", "correlacoes": correlacoes, "alerta": alerta}
        except Exception as e:
            logger.error(f"[Correlatos] Erro: {e}")
            return {"status": "ERRO", "correlacoes": {}, "alerta": str(e)}

