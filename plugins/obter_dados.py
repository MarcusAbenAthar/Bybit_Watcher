"""Plugin para obter dados de mercado (candles) usando a conexão autenticada."""

from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)

import requests

class ObterDados(Plugin):
    """
    Plugin para obtenção de dados externos (FGI, LSR, BTC.d, etc).
    - Responsabilidade única: coleta de dados de fontes externas.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "obter_dados"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["dados", "externos", "coleta"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin ObterDados.
        """
        return []

    """
    Plugin responsável por buscar dados crus (candles) da Bybit e popular dados_completos["candles"].

    - Consome a dependência obrigatória: conexao (plugin de autenticação).
    - Não gerencia autenticação, apenas requisita dados usando o cliente fornecido.
    - Responsabilidade única: obter e validar candles.
    """

    PLUGIN_NAME = "obter_dados"
    PLUGIN_CATEGORIA = "infraestrutura"
    PLUGIN_TAGS = ["dados", "candles", "mercado"]
    PLUGIN_PRIORIDADE = 15

    def __init__(self, conexao, **kwargs):
        """
        Inicializa o plugin com a dependência de conexão.
        """
        super().__init__(**kwargs)
        self._conexao = conexao

    def executar(self, dados_completos: dict, symbol: str, timeframe: str, limit: int = 200) -> bool:
        """
        Busca candles da Bybit e popula dados_completos['crus'] com os dados crus (lista de k-lines).
        Também mantém compatibilidade preenchendo dados_completos['candles'].

        Args:
            dados_completos (dict): Dicionário compartilhado do pipeline.
            symbol (str): Par de negociação (ex: "BTC/USDT").
            timeframe (str): Timeframe (ex: "1m", "5m").
            limit (int): Quantidade de candles a buscar.

        Returns:
            bool: True mesmo em caso de erro (para não interromper pipeline).
        """
        resultado_padrao = []

        try:
            cliente = self._conexao.obter_cliente()
            if not cliente:
                logger.error(f"[{self.nome}] Cliente Bybit não disponível.")
                dados_completos["crus"] = resultado_padrao
                dados_completos["candles"] = resultado_padrao  # compatibilidade
                return True

            # Ajusta simbolo para formato CCXT usando Conexao
            if hasattr(self._conexao, "listar_pares"):
                self._conexao.listar_pares()
            info = self._conexao.obter_info_par(symbol)
            exchange_symbol = info.get("symbol", symbol) if info else symbol
            candles = cliente.fetch_ohlcv(exchange_symbol, timeframe, limit=limit)
            if not candles or not isinstance(candles, list):
                logger.warning(f"[{self.nome}] Nenhum candle recebido para {symbol}-{timeframe}.")
                dados_completos["crus"] = resultado_padrao
                dados_completos["candles"] = resultado_padrao
                return True

            # Validação básica do formato dos candles
            for c in candles:
                if not isinstance(c, list) or len(c) < 5:
                    logger.error(f"[{self.nome}] Candle malformado: {c}")
                    dados_completos["crus"] = resultado_padrao
                    dados_completos["candles"] = resultado_padrao
                    return True

            # Preenche tanto 'crus' (preferencial) quanto 'candles' (legado)
            dados_completos["crus"] = candles
            dados_completos["candles"] = candles
            logger.info(f"[{self.nome}] Candles crus populados para {symbol}-{timeframe} ({len(candles)})")
            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao obter candles: {e}", exc_info=True)
            dados_completos["crus"] = resultado_padrao
            dados_completos["candles"] = resultado_padrao
            return True

    def obter_fear_greed_index(self) -> dict:
        """
        Obtém o índice Fear & Greed do mercado cripto via API pública.
        Retorna dict com valor atual, classificação textual e timestamp.
        Fonte e thresholds são definidos em config/env.
        """
        from utils.config import carregar_config
        import time
        config = carregar_config()
        url = config.get('FGI_URL', 'https://api.alternative.me/fng/')
        cache_key = '_cache_fgi'
        cache_ttl = int(config.get('FGI_CACHE_TTL', 300))  # segundos
        now = int(time.time())
        if hasattr(self, cache_key):
            cache = getattr(self, cache_key)
            if now - cache.get('timestamp', 0) < cache_ttl:
                logger.debug('[obter_dados] FGI cache hit')
                return cache['data']
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    info = data["data"][0]
                    fgi = {
                        "value": int(info["value"]),
                        "classification": info["value_classification"],
                        "timestamp": int(info["timestamp"]),
                        "fonte": url
                    }
                    setattr(self, cache_key, {"timestamp": now, "data": fgi})
                    logger.info(f"[obter_dados] Fear & Greed Index: {fgi}")
                    return fgi
            logger.warning("[obter_dados] Não foi possível obter o Fear & Greed Index.")
            return {"value": None, "classification": None, "timestamp": None, "fonte": url}
        except Exception as e:
            logger.error(f"[obter_dados] Erro ao buscar Fear & Greed Index: {e}")
            return {"value": None, "classification": None, "timestamp": None, "fonte": url}

    def obter_long_short_ratio(self, symbol: str = 'BTCUSDT') -> dict:
        """
        Obtém o Long/Short Ratio (LSR) de uma exchange, configurável via config/env.
        Implementa cache inteligente e logs claros. Nunca hardcoded.
        Args:
            symbol (str): Símbolo do ativo (ex: BTCUSDT)
        Returns:
            dict: {'lsr': float, 'long': float, 'short': float, 'direcao': str, 'fonte': str, 'timestamp': int}
        """
        from utils.config import carregar_config
        import time
        config = carregar_config()
        url = config.get('LSR_URL', '').format(symbol=symbol)
        cache_key = f'_cache_lsr_{symbol}'
        cache_ttl = int(config.get('LSR_CACHE_TTL', 300))
        now = int(time.time())
        if hasattr(self, cache_key):
            cache = getattr(self, cache_key)
            if now - cache.get('timestamp', 0) < cache_ttl:
                logger.debug(f'[obter_dados] LSR cache hit para {symbol}')
                return cache['data']
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # O formato esperado deve ser padronizado via config/env
                lsr = float(data.get('longShortRatio', 1.0))
                long_pct = float(data.get('longAccount', 0.0))
                short_pct = float(data.get('shortAccount', 0.0))
                direcao = (
                    'Long Pesado' if lsr > float(config.get('LSR_LIMITE_LONG', 1.5)) else
                    'Short Pesado' if lsr < float(config.get('LSR_LIMITE_SHORT', 0.7)) else
                    'Equilibrado'
                )
                resultado = {
                    'lsr': lsr,
                    'long': long_pct,
                    'short': short_pct,
                    'direcao': direcao,
                    'fonte': url,
                    'timestamp': now
                }
                setattr(self, cache_key, {"timestamp": now, "data": resultado})
                logger.info(f"[obter_dados] LSR: {resultado}")
                return resultado
            logger.warning(f"[obter_dados] Não foi possível obter o LSR para {symbol}.")
            return {'lsr': None, 'long': None, 'short': None, 'direcao': None, 'fonte': url, 'timestamp': now}
        except Exception as e:
            logger.error(f"[obter_dados] Erro ao buscar LSR: {e}")
            return {'lsr': None, 'long': None, 'short': None, 'direcao': None, 'fonte': url, 'timestamp': now}

    def obter_btc_dominance(self) -> dict:
        """
        Obtém o BTC Dominance (BTC.d) de fonte configurável.
        Implementa cache, categorização e logs claros.
        Returns:
            dict: {'dominance': float, 'direcao': str, 'categoria': str, 'fonte': str, 'timestamp': int}
        """
        from utils.config import carregar_config
        import time
        config = carregar_config()
        url = config.get('BTC_DOMINANCE_URL', '')
        cache_key = '_cache_btc_dominance'
        cache_ttl = int(config.get('BTC_DOMINANCE_CACHE_TTL', 300))
        now = int(time.time())
        if hasattr(self, cache_key):
            cache = getattr(self, cache_key)
            if now - cache.get('timestamp', 0) < cache_ttl:
                logger.debug('[obter_dados] BTC.d cache hit')
                return cache['data']
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                dominance = float(data.get('btc_dominance', 0.0))
                direcao = data.get('direction', 'Estável')
                categoria = (
                    'Alta' if dominance >= float(config.get('BTC_DOMINANCE_LIMITE_ALTA', 50)) else
                    'Baixa' if dominance <= float(config.get('BTC_DOMINANCE_LIMITE_BAIXA', 45)) else
                    'Média'
                )
                resultado = {
                    'dominance': dominance,
                    'direcao': direcao,
                    'categoria': categoria,
                    'fonte': url,
                    'timestamp': now
                }
                setattr(self, cache_key, {"timestamp": now, "data": resultado})
                logger.info(f"[obter_dados] BTC Dominance: {resultado}")
                return resultado
            logger.warning('[obter_dados] Não foi possível obter BTC Dominance.')
            return {'dominance': None, 'direcao': None, 'categoria': None, 'fonte': url, 'timestamp': now}
        except Exception as e:
            logger.error(f"[obter_dados] Erro ao buscar BTC Dominance: {e}")
            return {'dominance': None, 'direcao': None, 'categoria': None, 'fonte': url, 'timestamp': now}
