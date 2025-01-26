from loguru import logger
import psycopg2
from .plugin import Plugin
import talib


class AnaliseCandles(Plugin):
    """
    Plugin para analisar os candles e identificar padrões.
    """

    def __init__(self, config):
        super().__init__(config)

    def identificar_padrao(self, candle):
        """
        Identifica o padrão do candle usando TA-Lib.

        Args:
            candle (list): Lista com os dados do candle [abertura, fechamento, máximo, mínimo].

        Returns:
            str: Nome do padrão identificado ou None se nenhum padrão for identificado.
        """
        abertura, fechamento, maximo, minimo = candle

        # Converte os dados do candle para o formato aceito pelo TA-Lib
        candle_data = {
            "open": abertura,
            "high": maximo,
            "low": minimo,
            "close": fechamento,
        }

        # Identifica o padrão do candle usando a função CDL do TA-Lib
        padrao = talib.CDL(candle_data)

        # Mapeia os códigos numéricos dos padrões para nomes mais descritivos
        padroes = {
            talib.CDL2CROWS: "two_crows",
            talib.CDL3BLACKCROWS: "three_black_crows",
            talib.CDL3INSIDE: "three_inside_up_down",
            talib.CDL3LINESTRIKE: "three_line_strike",
            talib.CDL3OUTSIDE: "three_outside_up_down",
            talib.CDL3STARSINSOUTH: "three_stars_in_the_south",
            talib.CDL3WHITESOLDIERS: "three_white_soldiers",
            talib.CDLABANDONEDBABY: "abandoned_baby",
            talib.CDLADVANCEBLOCK: "advance_block",
            talib.CDLBELTHOLD: "belt_hold",
            talib.CDLBREAKAWAY: "breakaway",
            talib.CDLCLOSINGMARUBOZU: "closing_marubozu",
            talib.CDLCONCEALBABYSWALL: "concealing_baby_swallow",
            talib.CDLCOUNTERATTACK: "counterattack",
            talib.CDLDARKCLOUDCOVER: "dark_cloud_cover",
            talib.CDLDOJI: "doji",
            talib.CDLDOJISTAR: "doji_star",
            talib.CDLDRAGONFLYDOJI: "dragonfly_doji",
            talib.CDLENGULFING: "engulfing",
            talib.CDLEVENINGDOJISTAR: "evening_doji_star",
            talib.CDLEVENINGSTAR: "evening_star",
            talib.CDLGAPSIDESIDEWHITE: "gap_side_side_white",
            talib.CDLGRAVESTONEDOJI: "gravestone_doji",
            talib.CDLHAMMER: "hammer",
            talib.CDLHANGINGMAN: "hanging_man",
            talib.CDLHARAMI: "harami",
            talib.CDLHARAMICROSS: "harami_cross",
            talib.CDLHIGHWAVE: "high_wave",
            talib.CDLHIKKAKE: "hikkake",
            talib.CDLHIKKAKEMOD: "modified_hikkake",
            talib.CDLHOMINGPIGEON: "homing_pigeon",
            talib.CDLIDENTICAL3CROWS: "identical_three_crows",
            talib.CDLINNECK: "in_neck",
            talib.CDLINVERTEDHAMMER: "inverted_hammer",
            talib.CDLKICKING: "kicking",
            talib.CDLKICKINGBYLENGTH: "kicking_by_length",
            talib.CDLLADDERBOTTOM: "ladder_bottom",
            talib.CDLLONGLEGGEDDOJI: "long_legged_doji",
            talib.CDLLONGLINE: "long_line",
            talib.CDLMARUBOZU: "marubozu",
            talib.CDLMATCHINGLOW: "matching_low",
            talib.CDLMATHOLD: "mat_hold",
            talib.CDLMORNINGDOJISTAR: "morning_doji_star",
            talib.CDLMORNINGSTAR: "morning_star",
            talib.CDLONNECK: "on_neck",
            talib.CDLPIERCING: "piercing",
            talib.CDLRICKSHAWMAN: "rickshaw_man",
            talib.CDLRISEFALL3METHODS: "rise_fall_three_methods",
            talib.CDLSEPARATINGLINES: "separating_lines",
            talib.CDLSHOOTINGSTAR: "shooting_star",
            talib.CDLSHORTLINE: "short_line",
            talib.CDLSPINNINGTOP: "spinning_top",
            talib.CDLSTALLEDPATTERN: "stalled_pattern",
            talib.CDLSTICKSANDWICH: "stick_sandwich",
            talib.CDLTAKURI: "takuri",
            talib.CDLTASUKIGAP: "tasuki_gap",
            talib.CDLTHRUSTING: "thrusting",
            talib.CDLTRISTAR: "tristar",
            talib.CDLUNIQUE3RIVER: "unique_three_river",
            talib.CDLUPSIDEGAP2CROWS: "upside_gap_two_crows",
            talib.CDLXSIDEGAP3METHODS: "xside_gap_three_methods",
        }

        # Retorna o nome do padrão ou None se não for encontrado
        return padroes.get(padrao)

    def classificar_candle(self, candle):
        """
        Classifica o candle como alta, baixa ou indecisão.

        Args:
            candle (list): Lista com os dados do candle (abertura, fechamento, máximo, mínimo).

        Returns:
            str: Classificação do candle ("alta", "baixa" ou "indecisão").
        """
        abertura, fechamento, maximo, minimo = candle

        # Calcula o tamanho do corpo do candle
        tamanho_corpo = abs(fechamento - abertura)

        # Define um limite para considerar um candle como "pequeno"
        limite_corpo_pequeno = 0.1 * (maximo - minimo)  # 10% da amplitude do candle

        # Classifica o candle
        if tamanho_corpo <= limite_corpo_pequeno:
            return "indecisão"  # Doji ou candle com corpo muito pequeno
        elif fechamento > abertura:
            return "alta"
        else:
            return "baixa"


def gerar_sinal(self, data, padrao, classificacao):
    """
    Gera um sinal de compra ou venda com base no padrão e na classificação do candle.

    Args:
        data (list): Dados do candle.
        padrao (str): Nome do padrão identificado.
        classificacao (str): Classificação do candle.

    Returns:
        dict: Um dicionário com o sinal, o stop loss e o take profit.
    """
    sinal = None
    stop_loss = None
    take_profit = None

    if padrao == "martelo" and classificacao == "alta":
        sinal = "compra"
        stop_loss = data[3]  # Stop loss no mínimo do candle
        take_profit = data[2] + 2 * (
            data[1] - data[3]
        )  # Take profit 2 vezes o tamanho do corpo acima do máximo

    elif padrao == "estrela_cadente" and classificacao == "baixa":
        sinal = "venda"
        stop_loss = data[2]  # Stop loss no máximo do candle
        take_profit = data[3] - 2 * (
            data[0] - data[1]
        )  # Take profit 2 vezes o tamanho do corpo abaixo do mínimo

    # ... (adicionar lógica para outros padrões e classificações) ...

    return {
        "sinal": sinal,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
    }


def executar(self, dados, par, timeframe):
    """
    Executa a análise dos candles e salva os resultados no banco de dados.

    Args:
        dados (list): Lista de candles.
        par (str): Par de moedas.
        timeframe (str): Timeframe dos candles.
    """
    try:
        conn = self.banco_dados.conn
        cursor = conn.cursor()

        for candle in dados:
            # Identifica o padrão do candle
            padrao = self.identificar_padrao(candle)

            # Classifica o candle
            classificacao = self.classificar_candle(candle)

            # Gera o sinal de compra ou venda
            sinal = self.gerar_sinal(candle, padrao, classificacao)

            # Salva os dados no banco de dados
            timestamp = int(candle[0] / 1000)  # Converte o timestamp para segundos
            cursor.execute(
                """
                INSERT INTO analise_candles (par, timeframe, timestamp, padrao, classificacao, sinal, stop_loss, take_profit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (par, timeframe, timestamp) DO UPDATE
                SET padrao = EXCLUDED.padrao, classificacao = EXCLUDED.classificacao,
                    sinal = EXCLUDED.sinal, stop_loss = EXCLUDED.stop_loss, take_profit = EXCLUDED.take_profit;
                """,
                (
                    par,
                    timeframe,
                    timestamp,
                    padrao,
                    classificacao,
                    sinal["sinal"],
                    sinal["stop_loss"],
                    sinal["take_profit"],
                ),
            )

        conn.commit()
        logger.debug(f"Análise de candles para {par} - {timeframe} concluída.")

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Erro ao analisar candles: {error}")
