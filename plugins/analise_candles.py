from loguru import logger

import psycopg2
from plugins.plugin import Plugin
from plugins.gerente_plugin import obter_calculo_alavancagem, obter_banco_dados
import talib
from utils.padroes_candles import PADROES_CANDLES


class AnaliseCandles(Plugin):
    """
    Plugin para analisar os candles e identificar padrões.
    """

    def __init__(self):
        super().__init__()
        self.calculo_alavancagem = obter_calculo_alavancagem()

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
            talib.CDL2CROWS: "dois_corvos",
            talib.CDL3BLACKCROWS: "tres_corvos_negros",
            talib.CDL3INSIDE: "tres_dentro_cima_baixo",
            talib.CDL3LINESTRIKE: "golpe_de_tres_linhas",
            talib.CDL3OUTSIDE: "tres_fora_cima_baixo",
            talib.CDL3STARSINSOUTH: "tres_estrelas_no_sul",
            talib.CDL3WHITESOLDIERS: "tres_soldados_brancos",
            talib.CDLABANDONEDBABY: "bebe_abandonado",
            talib.CDLADVANCEBLOCK: "avanco_de_bloco",
            talib.CDLBELTHOLD: "cinturao",
            talib.CDLBREAKAWAY: "rompimento",
            talib.CDLCLOSINGMARUBOZU: "fechamento_marubozu",
            talib.CDLCONCEALBABYSWALL: "engolimento_de_bebe",
            talib.CDLCOUNTERATTACK: "contra_ataque",
            talib.CDLDARKCLOUDCOVER: "cobertura_de_nuvem_escura",
            talib.CDLDOJI: "doji",
            talib.CDLDOJISTAR: "doji_estrela",
            talib.CDLDRAGONFLYDOJI: "libelula_doji",
            talib.CDLENGULFING: "engolfo",
            talib.CDLEVENINGDOJISTAR: "estrela_da_noite_doji",
            talib.CDLEVENINGSTAR: "estrela_da_noite",
            talib.CDLGAPSIDESIDEWHITE: "lacuna_lateral_lado_branco",
            talib.CDLGRAVESTONEDOJI: "lapide_doji",
            talib.CDLHAMMER: "martelo",
            talib.CDLHANGINGMAN: "enforcado",
            talib.CDLHARAMI: "harami",
            talib.CDLHARAMICROSS: "harami_cruzado",
            talib.CDLHIGHWAVE: "onda_alta",
            talib.CDLHIKKAKE: "hikkake",
            talib.CDLHIKKAKEMOD: "hikkake_modificado",
            talib.CDLHOMINGPIGEON: "pombo_correio",
            talib.CDLIDENTICAL3CROWS: "tres_corvos_identicos",
            talib.CDLINNECK: "pescoco_interno",
            talib.CDLINVERTEDHAMMER: "martelo_invertido",
            talib.CDLKICKING: "chute",
            talib.CDLKICKINGBYLENGTH: "chute_por_comprimento",
            talib.CDLLADDERBOTTOM: "fundo_de_escada",
            talib.CDLLONGLEGGEDDOJI: "doji_pernas_longas",
            talib.CDLLONGLINE: "linha_longa",
            talib.CDLMARUBOZU: "marubozu",
            talib.CDLMATCHINGLOW: "minima_correspondente",
            talib.CDLMATHOLD: "mat_hold",
            talib.CDLMORNINGDOJISTAR: "estrela_da_manha_doji",
            talib.CDLMORNINGSTAR: "estrela_da_manha",
            talib.CDLONNECK: "pescoco_externo",
            talib.CDLPIERCING: "piercing",
            talib.CDLRICKSHAWMAN: "homem_de_riquixa",
            talib.CDLRISEFALL3METHODS: "subida_e_queda_tres_metodos",
            talib.CDLSEPARATINGLINES: "linhas_separadoras",
            talib.CDLSHOOTINGSTAR: "estrela_cadente",
            talib.CDLSHORTLINE: "linha_curta",
            talib.CDLSPINNINGTOP: "pião",
            talib.CDLSTALLEDPATTERN: "padrao_estagnado",
            talib.CDLSTICKSANDWICH: "sanduiche_de_velas",
            talib.CDLTAKURI: "takuri",
            talib.CDLTASUKIGAP: "lacuna_tasuki",
            talib.CDLTHRUSTING: "empurrando",
            talib.CDLTRISTAR: "tri_estrela",
            talib.CDLUNIQUE3RIVER: "tres_rios_unicos",
            talib.CDLUPSIDEGAP2CROWS: "lacuna_de_alta_dois_corvos",
            talib.CDLXSIDEGAP3METHODS: "lacuna_lateral_tres_metodos",
        }

        # Retorna o nome do padrão ou None se não for encontrado
        return padroes.get(padrao)

    def classificar_candle(self, candle):
        """
        Classifica o candle como alta, baixa ou indecisão, seguindo as Regras de Ouro.

        Args:
            candle (list): Lista com os dados do candle (abertura, fechamento, máximo, mínimo).

        Returns:
            str: Classificação do candle ("alta", "baixa" ou "indecisão").
        """
        abertura, fechamento, maximo, minimo = candle

        # Calcula o tamanho do corpo do candle
        tamanho_corpo = abs(fechamento - abertura)

        # Define um limite para considerar um candle como "pequeno" (Regra de Ouro: Critério)
        limite_corpo_pequeno = 0.1 * (maximo - minimo)  # 10% da amplitude do candle

        # Classifica o candle (Regra de Ouro: Clareza)
        if tamanho_corpo <= limite_corpo_pequeno:
            return "indecisão"  # Doji ou candle com corpo muito pequeno
        elif fechamento > abertura:
            return "alta"
        else:
            return "baixa"

    def gerar_sinal(self, dados, padrao, classificacao, par, timeframe, config):
        """
        Gera um sinal de compra ou venda com base no padrão e na classificação do candle.
        """
        sinal = None
        stop_loss = None
        take_profit = None

        chave_padrao = f"{padrao}_{classificacao}"
        # Verifica se a chave existe no dicionário de padrões
        if chave_padrao in PADROES_CANDLES:
            # Obtém a lógica para o padrão
            logica = PADROES_CANDLES[chave_padrao]
            sinal = logica["sinal"]

            # Calcula a alavancagem ideal (Regra de Ouro: Dinamismo)
            alavancagem = self.calculo_alavancagem.calcular_alavancagem(
                dados[-1], par, timeframe, config
            )

            # Calcula o stop loss e o take profit, passando a alavancagem como argumento
            stop_loss = logica["stop_loss"](dados, alavancagem)
            take_profit = logica["take_profit"](dados, alavancagem)

        return {
            "sinal": sinal,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }

    def executar(self, dados, par, timeframe, config):
        """
        Executa a análise dos candles, gera sinais de trading e salva os resultados no banco de dados.
        """
        try:
            # Usa a conexão com o banco de dados fornecida pelo Core
            conn = obter_banco_dados().conn
            cursor = conn.cursor()

            for candle in dados:
                padrao = self.identificar_padrao(candle)
                classificacao = self.classificar_candle(candle)

                sinal = self.gerar_sinal(
                    candle, padrao, classificacao, par, timeframe, config
                )

                timestamp = int(candle / 1000)

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
