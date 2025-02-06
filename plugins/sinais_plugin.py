from plugins.plugin import Plugin
from loguru import logger


class SinaisPlugin(Plugin):
    """
    Plugin responsável por consolidar e gerenciar sinais de trading.

    Este plugin recebe sinais de diferentes indicadores, consolida as informações
    e gera um log estruturado que pode ser usado para notificações.

    Attributes:
        nome (str): Nome do plugin
        config (dict): Configurações do plugin
    """

    def __init__(self, config=None):
        """
        Inicializa o plugin de sinais.

        Args:
            config (dict, optional): Configurações do plugin
        """
        super().__init__()
        self.nome = "Sinais"
        self.config = config

    def executar(self, dados, symbol, timeframe):
        """
        Executa a análise e consolidação dos sinais.

        Args:
            dados (dict): Dicionário contendo os sinais dos diferentes indicadores
            symbol (str): Símbolo do par analisado
            timeframe (str): Timeframe da análise

        Returns:
            dict: Sinal consolidado com todas as informações relevantes
        """
        try:
            if not dados:  # Se dados for None ou vazio
                return None

            sinal_consolidado = self.consolidar_sinais(dados)
            if sinal_consolidado:
                self.logar_sinal(sinal_consolidado, symbol, timeframe)

            return sinal_consolidado

        except Exception as e:
            logger.error(f"Erro ao processar sinais: {e}")
            return None

    def consolidar_sinais(self, dados):
        """
        Consolida os sinais de diferentes indicadores em um único sinal.

        Args:
            dados (dict): Dicionário com os sinais dos indicadores

        Returns:
            dict: Sinal consolidado com direção, força e confiança
        """
        try:
            if dados is None:
                return None  # Retorna None em vez de um dicionário vazio

            direcao = self.determinar_direcao(dados)
            forca = self.calcular_forca(dados)
            confianca = self.calcular_confianca(dados)

            return {
                "direcao": direcao,
                "forca": forca,
                "confianca": confianca,
                "indicadores": dados,
            }

        except Exception as e:
            logger.error(f"Erro ao consolidar sinais: {e}")
            return None

    def determinar_direcao(self, dados):
        """
        Determina a direção do sinal com base nos indicadores.

        Args:
            dados (dict): Dicionário com os sinais dos indicadores

        Returns:
            str: Direção do sinal ('ALTA', 'BAIXA' ou 'NEUTRO')
        """
        try:
            sinais_alta = 0
            sinais_baixa = 0
            peso_total = 0

            # Analisa tendência
            if "tendencia" in dados:
                peso = 3  # Peso maior para indicadores de tendência
                peso_total += peso
                if dados["tendencia"]["direcao"] == "ALTA":
                    sinais_alta += peso
                elif dados["tendencia"]["direcao"] == "BAIXA":
                    sinais_baixa += peso

            # Analisa médias móveis
            if "medias_moveis" in dados:
                peso = 2
                peso_total += peso
                if dados["medias_moveis"]["direcao"] == "ALTA":
                    sinais_alta += peso
                elif dados["medias_moveis"]["direcao"] == "BAIXA":
                    sinais_baixa += peso

            # Calcula percentual de concordância
            if peso_total > 0:
                concordancia_alta = (sinais_alta / peso_total) * 100
                concordancia_baixa = (sinais_baixa / peso_total) * 100

                if concordancia_alta >= 60:
                    return "ALTA"
                elif concordancia_baixa >= 60:
                    return "BAIXA"

            return "NEUTRO"

        except Exception as e:
            logger.error(f"Erro ao determinar direção: {e}")
            return "NEUTRO"

    def calcular_forca(self, dados):
        """
        Calcula a força do sinal com base nos indicadores.

        Args:
            dados (dict): Dicionário com os sinais dos indicadores

        Returns:
            str: Força do sinal ('FORTE', 'MÉDIA' ou 'FRACA')
        """
        try:
            forca_total = 0
            peso_total = 0

            if "tendencia" in dados:
                peso = 3
                peso_total += peso
                if dados["tendencia"]["forca"] == "FORTE":
                    forca_total += peso * 3
                elif dados["tendencia"]["forca"] == "MÉDIA":
                    forca_total += peso * 2
                elif dados["tendencia"]["forca"] == "FRACA":
                    forca_total += peso

            if "medias_moveis" in dados:
                peso = 2
                peso_total += peso
                if dados["medias_moveis"]["forca"] == "FORTE":
                    forca_total += peso * 3
                elif dados["medias_moveis"]["forca"] == "MÉDIA":
                    forca_total += peso * 2
                elif dados["medias_moveis"]["forca"] == "FRACA":
                    forca_total += peso

            if peso_total > 0:
                forca_media = (forca_total / (peso_total * 3)) * 100

                if forca_media >= 85:  # Ajustado para 85%
                    return "FORTE"
                elif forca_media >= 40:
                    return "MÉDIA"

            return "FRACA"

        except Exception as e:
            logger.error(f"Erro ao calcular força: {e}")
            return "FRACA"

    def calcular_confianca(self, dados):
        """
        Calcula o nível de confiança do sinal.

        Args:
            dados (dict): Dicionário com os sinais dos indicadores

        Returns:
            float: Percentual de confiança (0-100)
        """
        try:
            confianca_total = 0
            peso_total = 0

            # Soma confiança ponderada de cada indicador
            if "tendencia" in dados:
                peso = 3
                peso_total += peso
                confianca_total += dados["tendencia"]["confianca"] * peso

            if "medias_moveis" in dados:
                peso = 2
                peso_total += peso
                confianca_total += dados["medias_moveis"]["confianca"] * peso

            # Calcula média ponderada
            if peso_total > 0:
                return round(confianca_total / peso_total, 2)

            return 0.0

        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.0

    def logar_sinal(self, symbol, timeframe, sinal):
        """
        Gera um log estruturado do sinal.

        Args:
            symbol (str): Símbolo do par
            timeframe (str): Timeframe da análise
            sinal (dict): Sinal consolidado

        Returns:
            dict: Sinal formatado
        """
        try:
            if not all([symbol, timeframe, sinal]):
                raise ValueError("Parâmetros inválidos")

            sinal_formatado = {
                "symbol": symbol,
                "timeframe": timeframe,
                "direcao": sinal if isinstance(sinal, str) else sinal.get("direcao"),
                "forca": sinal.get("forca") if isinstance(sinal, dict) else None,
                "confianca": (
                    sinal.get("confianca") if isinstance(sinal, dict) else None
                ),
            }

            logger.info(
                "SINAL | "
                f"Symbol: {sinal_formatado['symbol']} | "
                f"Timeframe: {sinal_formatado['timeframe']} | "
                f"Direção: {sinal_formatado['direcao']}"
            )

            return sinal_formatado

        except Exception as e:
            logger.error(f"Erro ao logar sinal: {e}")
            raise
