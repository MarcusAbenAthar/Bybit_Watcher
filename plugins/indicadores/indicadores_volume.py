from loguru import logger
import psycopg2
import talib
from plugins.plugin import Plugin


class IndicadoresVolume(Plugin):
    """
    Plugin para calcular indicadores de volume e gerar sinais de trading,
    seguindo as Regras de Ouro.
    """

    def __init__(self, config, calculo_alavancagem):
        """
        Inicializa o plugin.
        """
        super().__init__(config)
        self.calculo_alavancagem = calculo_alavancagem

    def calcular_obv(self, dados):
        """
        Calcula o On Balance Volume (OBV) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.

        Returns:
            list: Lista com os valores do OBV.
        """
        fechamentos = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]
        return talib.OBV(fechamentos, volume)

    def calcular_cmf(self, dados, periodo=20):
        """
        Calcula o Chaikin Money Flow (CMF) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do CMF.

        Returns:
            list: Lista com os valores do CMF.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]
        return talib.CMF(high, low, close, volume, timeperiod=periodo)

    def calcular_mfi(self, dados, periodo=14):
        """
        Calcula o Índice de Fluxo de Dinheiro (MFI) para os dados fornecidos, usando a biblioteca TA-Lib.

        Args:
            dados (list): Lista de candles.
            periodo (int): Período do MFI.

        Returns:
            list: Lista com os valores do MFI.
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]
        return talib.MFI(high, low, close, volume, timeperiod=periodo)


def gerar_sinal(self, dados, indicador, tipo, par, timeframe):
    """
    Gera um sinal de compra ou venda com base no indicador de volume fornecido,
    seguindo as Regras de Ouro.

    Args:
        dados (list): Lista de candles.
        indicador (str): Nome do indicador de volume ("obv", "cmf" ou "mfi").
        tipo (str): Tipo de sinal (depende do indicador).
        par (str): Par de moedas.
        timeframe (str): Timeframe dos candles.

    Returns:
        dict: Um dicionário com o sinal, o stop loss e o take profit.
    """
    try:
        sinal = None
        stop_loss = None
        take_profit = None

        # Calcula a alavancagem ideal (Regra de Ouro: Dinamismo)
        alavancagem = self.calculo_alavancagem.calcular_alavancagem(
            dados[-1], par, timeframe
        )

        if indicador == "obv":
            obv = self.calcular_obv(dados)
            # Lógica para gerar sinais com base no OBV (exemplo: divergência)
            if tipo == "divergencia_altista" and self.detectar_divergencia_altista(
                dados, obv
            ):
                sinal = "compra"
                stop_loss = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                    0.1 / alavancagem
                )
                take_profit = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                    2 / alavancagem
                )
            elif tipo == "divergencia_baixista" and self.detectar_divergencia_baixista(
                dados, obv
            ):
                sinal = "venda"
                stop_loss = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                    0.1 / alavancagem
                )
                take_profit = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                    2 / alavancagem
                )

        elif indicador == "cmf":
            cmf = self.calcular_cmf(dados)
            # Lógica para gerar sinais com base no CMF (exemplo: cruzamento do zero)
            if tipo == "cruzamento_acima" and cmf[-1] > 0 and cmf[-2] < 0:
                sinal = "compra"
                stop_loss = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                    0.05 / alavancagem
                )
                take_profit = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                    1.5 / alavancagem
                )
            elif tipo == "cruzamento_abaixo" and cmf[-1] < 0 and cmf[-2] > 0:
                sinal = "venda"
                stop_loss = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                    0.05 / alavancagem
                )
                take_profit = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                    1.5 / alavancagem
                )

        elif indicador == "mfi":
            mfi = self.calcular_mfi(dados)
            # Lógica para gerar sinais com base no MFI (exemplo: sobrecompra/sobrevenda)
            if tipo == "sobrecompra" and mfi[-1] > 80:
                sinal = "venda"
                stop_loss = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                    0.05 / alavancagem
                )
                take_profit = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                    1.5 / alavancagem
                )
            elif tipo == "sobrevenda" and mfi[-1] < 20:
                sinal = "compra"
                stop_loss = dados[-1][3] - (dados[-1][2] - dados[-1][3]) * (
                    0.05 / alavancagem
                )
                take_profit = dados[-1][2] + (dados[-1][2] - dados[-1][3]) * (
                    1.5 / alavancagem
                )

        return {
            "sinal": sinal,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }

    except Exception as e:
        logger.error(f"Erro ao gerar sinal para {indicador} - {tipo}: {e}")
        return {
            "sinal": None,
            "stop_loss": None,
            "take_profit": None,
        }


def executar(self, dados, par, timeframe):
    """
    Executa o cálculo dos indicadores de volume, gera sinais de trading e salva os resultados no banco de dados.

    Args:
        dados (list): Lista de candles.
        par (str): Par de moedas.
        timeframe (str): Timeframe dos candles.
    """
    try:
        conn = self.banco_dados.conn
        cursor = conn.cursor()

        for candle in dados:
            # Calcula os indicadores de volume para o candle atual
            obv = self.calcular_obv([candle])
            cmf = self.calcular_cmf([candle])
            mfi = self.calcular_mfi([candle])

            # Gera os sinais de compra e venda para o candle atual
            sinal_obv_divergencia_altista = self.gerar_sinal(
                [candle], "obv", "divergencia_altista", par, timeframe
            )
            sinal_obv_divergencia_baixista = self.gerar_sinal(
                [candle], "obv", "divergencia_baixista", par, timeframe
            )
            sinal_cmf_cruzamento_acima = self.gerar_sinal(
                [candle], "cmf", "cruzamento_acima", par, timeframe
            )
            sinal_cmf_cruzamento_abaixo = self.gerar_sinal(
                [candle], "cmf", "cruzamento_abaixo", par, timeframe
            )
            sinal_mfi_sobrecompra = self.gerar_sinal(
                [candle], "mfi", "sobrecompra", par, timeframe
            )
            sinal_mfi_sobrevenda = self.gerar_sinal(
                [candle], "mfi", "sobrevenda", par, timeframe
            )

            # Salva os resultados no banco de dados para o candle atual
            timestamp = int(candle[0] / 1000)  # Converte o timestamp para segundos
            cursor.execute(
                """
                INSERT INTO indicadores_volume (
                    par, timeframe, timestamp, obv, cmf, mfi,
                    sinal_obv_divergencia_altista, stop_loss_obv_divergencia_altista, take_profit_obv_divergencia_altista,
                    sinal_obv_divergencia_baixista, stop_loss_obv_divergencia_baixista, take_profit_obv_divergencia_baixista,
                    sinal_cmf_cruzamento_acima, stop_loss_cmf_cruzamento_acima, take_profit_cmf_cruzamento_acima,
                    sinal_cmf_cruzamento_abaixo, stop_loss_cmf_cruzamento_abaixo, take_profit_cmf_cruzamento_abaixo,
                    sinal_mfi_sobrecompra, stop_loss_mfi_sobrecompra, take_profit_mfi_sobrecompra,
                    sinal_mfi_sobrevenda, stop_loss_mfi_sobrevenda, take_profit_mfi_sobrevenda
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (par, timeframe, timestamp) DO UPDATE
                SET obv = EXCLUDED.obv, cmf = EXCLUDED.cmf, mfi = EXCLUDED.mfi,
                    sinal_obv_divergencia_altista = EXCLUDED.sinal_obv_divergencia_altista, stop_loss_obv_divergencia_altista = EXCLUDED.stop_loss_obv_divergencia_altista, take_profit_obv_divergencia_altista = EXCLUDED.take_profit_obv_divergencia_altista,
                    sinal_obv_divergencia_baixista = EXCLUDED.sinal_obv_divergencia_baixista, stop_loss_obv_divergencia_baixista = EXCLUDED.stop_loss_obv_divergencia_baixista, take_profit_obv_divergencia_baixista = EXCLUDED.take_profit_obv_divergencia_baixista,
                    sinal_cmf_cruzamento_acima = EXCLUDED.sinal_cmf_cruzamento_acima, stop_loss_cmf_cruzamento_acima = EXCLUDED.stop_loss_cmf_cruzamento_acima, take_profit_cmf_cruzamento_acima = EXCLUDED.take_profit_cmf_cruzamento_acima,
                    sinal_cmf_cruzamento_abaixo = EXCLUDED.sinal_cmf_cruzamento_abaixo, stop_loss_cmf_cruzamento_abaixo = EXCLUDED.stop_loss_cmf_cruzamento_abaixo, take_profit_cmf_cruzamento_abaixo = EXCLUDED.take_profit_cmf_cruzamento_abaixo,
                    sinal_mfi_sobrecompra = EXCLUDED.sinal_mfi_sobrecompra, stop_loss_mfi_sobrecompra = EXCLUDED.stop_loss_mfi_sobrecompra, take_profit_mfi_sobrecompra = EXCLUDED.take_profit_mfi_sobrecompra,
                    sinal_mfi_sobrevenda = EXCLUDED.sinal_mfi_sobrevenda, stop_loss_mfi_sobrevenda = EXCLUDED.stop_loss_mfi_sobrevenda, take_profit_mfi_sobrevenda = EXCLUDED.take_profit_mfi_sobrevenda;
                """,
                (
                    par,
                    timeframe,
                    timestamp,
                    obv[-1],
                    cmf[-1],
                    mfi[-1],
                    sinal_obv_divergencia_altista["sinal"],
                    sinal_obv_divergencia_altista["stop_loss"],
                    sinal_obv_divergencia_altista["take_profit"],
                    sinal_obv_divergencia_baixista["sinal"],
                    sinal_obv_divergencia_baixista["stop_loss"],
                    sinal_obv_divergencia_baixista["take_profit"],
                    sinal_cmf_cruzamento_acima["sinal"],
                    sinal_cmf_cruzamento_acima["stop_loss"],
                    sinal_cmf_cruzamento_acima["take_profit"],
                    sinal_cmf_cruzamento_abaixo["sinal"],
                    sinal_cmf_cruzamento_abaixo["stop_loss"],
                    sinal_cmf_cruzamento_abaixo["take_profit"],
                    sinal_mfi_sobrecompra["sinal"],
                    sinal_mfi_sobrecompra["stop_loss"],
                    sinal_mfi_sobrecompra["take_profit"],
                    sinal_mfi_sobrevenda["sinal"],
                    sinal_mfi_sobrevenda["stop_loss"],
                    sinal_mfi_sobrevenda["take_profit"],
                ),
            )

        conn.commit()
        logger.debug(
            f"Indicadores de volume calculados e sinais gerados para {par} - {timeframe}."
        )

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Erro ao calcular indicadores de volume: {error}")
