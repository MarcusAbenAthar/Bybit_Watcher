# banco_dados.py
"""Plugin para operações de gravação no banco de dados."""

from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class BancoDados(Plugin):
    """Plugin para salvar dados no banco."""

    PLUGIN_NAME = "banco_dados"
    PLUGIN_TYPE = "essencial"

    def __init__(self, gerenciador_banco):
        """
        Inicializa o plugin com o gerenciador de banco.

        Args:
            gerenciador_banco: Instância do GerenciadorBanco (necessária pra conexão)
        """
        super().__init__()
        self._gerenciador = gerenciador_banco

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin, usando a conexão do gerenciador.

        Args:
            config: Configurações do bot

        Returns:
            bool: True se inicializado
        """
        try:
            if not super().inicializar(config):
                return False
            if not self._gerenciador.inicializado:
                self._gerenciador.inicializar(config)
            logger.info("BancoDados inicializado")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar BancoDados: {e}")
            return False

    def executar(self, *args, **kwargs) -> bool:
        """
        Salva dados no banco conforme o tipo.

        Args:
            dados: Dicionário com dados processados
            symbol: Símbolo do par
            timeframe: Timeframe
            tipo: Tipo de dado ("klines", "sinais", "indicadores_tendencia", etc.)

        Returns:
            bool: True se salvo com sucesso
        """
        try:
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            tipo = kwargs.get("tipo")
            if not all([dados, symbol, timeframe, tipo]):
                logger.error("Parâmetros insuficientes")
                return True

            if tipo == "klines" and isinstance(dados["crus"], list) and dados["crus"]:
                ultimo = dados["crus"][-1]
                query = """
                    INSERT INTO public.klines (symbol, timeframe, timestamp, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                params = (
                    symbol,
                    timeframe,
                    int(ultimo[0]),
                    float(ultimo[1]),
                    float(ultimo[2]),
                    float(ultimo[3]),
                    float(ultimo[4]),
                    float(ultimo[5]),
                )
                return self._gerenciador.executar(
                    query=query, params=params, commit=True
                )

            elif tipo == "sinais" and "sinais" in dados["processados"]:
                sinal = dados["processados"]["sinais"]
                query = """
                    INSERT INTO public.sinais (symbol, timeframe, tipo, sinal, forca, confianca, stop_loss, take_profit, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                params = (
                    symbol,
                    timeframe,
                    "consolidado",
                    sinal["direcao"],
                    sinal["forca"],
                    sinal["confianca"],
                    sinal.get("stop_loss"),
                    sinal.get("take_profit"),
                    int(dados["crus"][-1][0]),
                )
                return self._gerenciador.executar(
                    query=query, params=params, commit=True
                )

            elif tipo in [
                "indicadores_tendencia",
                "indicadores_osciladores",
                "indicadores_volatilidade",
                "indicadores_volume",
                "outros_indicadores",
            ]:
                indicadores = dados["processados"].get(tipo, {})
                if not indicadores:
                    return True
                timestamp = int(dados["crus"][-1][0]) if dados["crus"] else 0
                if tipo == "indicadores_tendencia":
                    query = """
                        INSERT INTO public.indicadores_tendencia (symbol, timeframe, timestamp, sma, ema)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                    params = (
                        symbol,
                        timeframe,
                        timestamp,
                        indicadores.get("sma"),
                        indicadores.get("ema"),
                    )
                elif tipo == "indicadores_osciladores":
                    query = """
                        INSERT INTO public.indicadores_osciladores (symbol, timeframe, timestamp, rsi, stochastic_k)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                    params = (
                        symbol,
                        timeframe,
                        timestamp,
                        indicadores.get("rsi"),
                        indicadores.get("stochastic_k"),
                    )
                elif tipo == "indicadores_volatilidade":
                    query = """
                        INSERT INTO public.indicadores_volatilidade (symbol, timeframe, timestamp, atr, bollinger_upper, bollinger_lower)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                    params = (
                        symbol,
                        timeframe,
                        timestamp,
                        indicadores.get("atr"),
                        indicadores.get("bollinger_upper"),
                        indicadores.get("bollinger_lower"),
                    )
                elif tipo == "indicadores_volume":
                    query = """
                        INSERT INTO public.indicadores_volume (symbol, timeframe, timestamp, obv, vwap)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                    params = (
                        symbol,
                        timeframe,
                        timestamp,
                        indicadores.get("obv"),
                        indicadores.get("vwap"),
                    )
                elif tipo == "outros_indicadores":
                    query = """
                        INSERT INTO public.outros_indicadores (symbol, timeframe, timestamp, tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, fibonacci_50, pivot_point)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING"""
                    ichimoku = indicadores.get("ichimoku", {})
                    fibonacci = indicadores.get("fibonacci", {})
                    pivot = indicadores.get("pivot_points", {})
                    params = (
                        symbol,
                        timeframe,
                        timestamp,
                        ichimoku.get("tenkan_sen"),
                        ichimoku.get("kijun_sen"),
                        ichimoku.get("senkou_span_a"),
                        ichimoku.get("senkou_span_b"),
                        fibonacci.get("50%"),
                        pivot.get("PP"),
                    )
                return self._gerenciador.executar(
                    query=query, params=params, commit=True
                )

            return True
        except Exception as e:
            logger.error(f"Erro ao salvar {tipo} no banco: {e}")
            return False

    def finalizar(self):
        """Finaliza o plugin."""
        try:
            logger.info("Finalizando BancoDados")
            # Não fecha a conexão aqui, pois é gerenciada pelo GerenciadorBanco
        except Exception as e:
            logger.error(f"Erro ao finalizar BancoDados: {e}")
