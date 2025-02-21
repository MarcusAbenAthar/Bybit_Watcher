import psycopg2
from plugins.gerenciadores.gerenciador_plugins import GerentePlugin
from utils.logging_config import get_logger
import talib
import numpy as np
from plugins.plugin import Plugin


logger = get_logger(__name__)


class IndicadoresVolume(Plugin):
    """
    Plugin para calcular indicadores de volume.
    """

    def __init__(self, gerente: GerentePlugin, config=None):
        """
        Inicializa o plugin IndicadoresVolume.

        Args:
            gerente: Instância do gerenciador de plugins
            config: Configurações do sistema
        """
        super().__init__()
        self.nome = "Indicadores de Volume"
        self.config = config
        self.gerente = gerente
        # Acessa o plugin de cálculo de alavancagem através do gerente
        self.calculo_alavancagem = self.gerente.obter_calculo_alavancagem()
        # Obtém o plugin de banco de dados através do gerente
        self.banco_dados = self.gerente.obter_banco_dados()

    def calcular_obv(self, dados):
        """
        Calcula o On Balance Volume (OBV).
        (sem alterações nesta função)
        """
        fechamentos = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]
        return talib.OBV(fechamentos, volume)

    def calcular_cmf(self, dados, periodo=20):
        """
        Calcula o Chaikin Money Flow (CMF).
        (sem alterações nesta função)
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]
        return talib.CMF(high, low, close, volume, timeperiod=periodo)

    def calcular_mfi(self, dados, periodo=14):
        """
        Calcula o Índice de Fluxo de Dinheiro (MFI).
        (sem alterações nesta função)
        """
        high = [candle[2] for candle in dados]
        low = [candle[3] for candle in dados]
        close = [candle[4] for candle in dados]
        volume = [candle[5] for candle in dados]
        return talib.MFI(high, low, close, volume, timeperiod=periodo)

    def gerar_sinal(self, dados, indicador, tipo, symbol, timeframe, config):
        """
        Gera um sinal de compra ou venda com base no indicador de volume fornecido.

        Args:
            dados (list): Lista de candles.
            indicador (str): Nome do indicador de volume ("obv", "cmf" ou "mfi").
            tipo (str): Tipo de sinal (depende do indicador).
            symbol (str): Par de moedas.
            timeframe (str): Timeframe dos candles.
            config (ConfigParser): Objeto com as configurações do bot.

        Returns:
            dict: Um dicionário com o sinal, o stop loss e o take profit.
        """
        try:
            sinal = None
            stop_loss = None
            take_profit = None

            # Calcula a alavancagem ideal (Regra de Ouro: Dinamismo)
            alavancagem = self.calculo_alavancagem.calcular_alavancagem(
                dados[-1], symbol, timeframe, config
            )

            if indicador == "obv":
                obv = self.calcular_obv(dados)
                # Lógica para gerar sinais com base no OBV (exemplo: divergência)
                if tipo == "divergencia_altista" and self.detectar_divergencia_altista(
                    dados, obv
                ):
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.1 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        2 / alavancagem
                    )
                elif (
                    tipo == "divergencia_baixista"
                    and self.detectar_divergencia_baixista(dados, obv)
                ):
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.1 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        2 / alavancagem
                    )

            elif indicador == "cmf":
                cmf = self.calcular_cmf(dados)
                # Lógica para gerar sinais com base no CMF (exemplo: cruzamento do zero)
                if tipo == "cruzamento_acima" and cmf[-1] > 0 and cmf[-2] < 0:
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )
                elif tipo == "cruzamento_abaixo" and cmf[-1] < 0 and cmf[-2] > 0:
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )

            elif indicador == "mfi":
                mfi = self.calcular_mfi(dados)
                # Lógica para gerar sinais com base no MFI (exemplo: sobrecompra/sobrevenda)
                if tipo == "sobrecompra" and mfi[-1] > 80:
                    sinal = "venda"
                    stop_loss = dados[-1] + (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] - (dados[-1] - dados[-1]) * (
                        1.5 / alavancagem
                    )
                elif tipo == "sobrevenda" and mfi[-1] < 20:
                    sinal = "compra"
                    stop_loss = dados[-1] - (dados[-1] - dados[-1]) * (
                        0.05 / alavancagem
                    )
                    take_profit = dados[-1] + (dados[-1] - dados[-1]) * (
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

    def executar(self, *args, **kwargs) -> bool:
        """
        Executa o cálculo dos indicadores de volume.

        Args:
            *args: Argumentos posicionais ignorados
            **kwargs: Argumentos nomeados contendo:
                dados (list): Lista de candles
                symbol (str): Símbolo do par
                timeframe (str): Timeframe da análise
                config (dict): Configurações do bot

        Returns:
            bool: True se executado com sucesso
        """
        try:
            # Extrai os parâmetros necessários
            dados = kwargs.get("dados")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")

            # Validação dos parâmetros
            if not all([dados, symbol, timeframe]):
                logger.error("Parâmetros necessários não fornecidos")
                dados["volume"] = {
                    "obv": None,
                    "cmf": None,
                    "mfi": None,
                    "sinais": {
                        "direcao": "NEUTRO",
                        "forca": "FRACA",
                        "confianca": 0,
                    },
                }
                return True

            # Verifica se o banco de dados está disponível e inicializado
            if not self.banco_dados or not hasattr(self.banco_dados, "conn"):
                logger.warning("Banco de dados não disponível")
                return True

            conn = self.banco_dados.conn
            if not conn:
                logger.warning("Conexão com banco de dados não disponível")
                return True

            cursor = conn.cursor()
            for candle in dados:
                # Calcula os indicadores de volume para o candle atual
                obv = self.calcular_obv([candle])
                cmf = self.calcular_cmf([candle])
                mfi = self.calcular_mfi([candle])

                # Gera os sinais de compra e venda para o candle atual
                sinal_obv_divergencia_altista = self.gerar_sinal(
                    [candle],
                    "obv",
                    "divergencia_altista",
                    symbol,
                    timeframe,
                    self.config,
                )

                sinal_obv_divergencia_baixista = self.gerar_sinal(
                    [candle],
                    "obv",
                    "divergencia_baixista",
                    symbol,
                    timeframe,
                    self.config,
                )
                sinal_cmf_cruzamento_acima = self.gerar_sinal(
                    [candle], "cmf", "cruzamento_acima", symbol, timeframe, self.config
                )
                sinal_cmf_cruzamento_abaixo = self.gerar_sinal(
                    [candle], "cmf", "cruzamento_abaixo", symbol, timeframe, self.config
                )
                sinal_mfi_sobrecompra = self.gerar_sinal(
                    [candle], "mfi", "sobrecompra", symbol, timeframe, self.config
                )
                sinal_mfi_sobrevenda = self.gerar_sinal(
                    [candle], "mfi", "sobrevenda", symbol, timeframe, self.config
                )

                # Salva os resultados no banco de dados para o candle atual
                timestamp = int(candle / 1000)  # Converte o timestamp para segundos
                cursor.execute(
                    """
                    INSERT INTO indicadores_volume (
                        symbol, timeframe, timestamp, obv, cmf, mfi,
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
                    ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE
                    SET obv = EXCLUDED.obv, cmf = EXCLUDED.cmf, mfi = EXCLUDED.mfi,
                        sinal_obv_divergencia_altista = EXCLUDED.sinal_obv_divergencia_altista, stop_loss_obv_divergencia_altista = EXCLUDED.stop_loss_obv_divergencia_altista, take_profit_obv_divergencia_altista = EXCLUDED.take_profit_obv_divergencia_altista,
                        sinal_obv_divergencia_baixista = EXCLUDED.sinal_obv_divergencia_baixista, stop_loss_obv_divergencia_baixista = EXCLUDED.stop_loss_obv_divergencia_baixista, take_profit_obv_divergencia_baixista = EXCLUDED.take_profit_obv_divergencia_baixista,
                        sinal_cmf_cruzamento_acima = EXCLUDED.sinal_cmf_cruzamento_acima, stop_loss_cmf_cruzamento_acima = EXCLUDED.stop_loss_cmf_cruzamento_acima, take_profit_cmf_cruzamento_acima = EXCLUDED.take_profit_cmf_cruzamento_acima,
                        sinal_cmf_cruzamento_abaixo = EXCLUDED.sinal_cmf_cruzamento_abaixo, stop_loss_cmf_cruzamento_abaixo = EXCLUDED.stop_loss_cmf_cruzamento_abaixo, take_profit_cmf_cruzamento_abaixo = EXCLUDED.take_profit_cmf_cruzamento_abaixo,
                        sinal_mfi_sobrecompra = EXCLUDED.sinal_mfi_sobrecompra, stop_loss_mfi_sobrecompra = EXCLUDED.stop_loss_mfi_sobrecompra, take_profit_mfi_sobrecompra = EXCLUDED.take_profit_mfi_sobrecompra,
                        sinal_mfi_sobrevenda = EXCLUDED.sinal_mfi_sobrevenda, stop_loss_mfi_sobrevenda = EXCLUDED.stop_loss_mfi_sobrevenda, take_profit_mfi_sobrevenda = EXCLUDED.take_profit_mfi_sobrevenda;
                    """,
                    (
                        symbol,
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
                f"Indicadores de volume calculados e sinais gerados para {symbol} - {timeframe}."
            )

        except (Exception, psycopg2.Error) as error:
            logger.error(f"Erro ao calcular indicadores de volume: {error}")
            dados["volume"] = {
                "obv": None,
                "cmf": None,
                "mfi": None,
                "sinais": {
                    "direcao": "NEUTRO",
                    "forca": "FRACA",
                    "confianca": 0,
                },
            }
            return True

        return True
