# sinais_plugin.py
from utils.logging_config import get_logger
from plugins.plugin import Plugin

logger = get_logger(__name__)


class SinaisPlugin(Plugin):
    """Plugin para gerenciamento de sinais de trading."""

    # Identificador explícito do plugin
    PLUGIN_NAME = "sinais_plugin"
    PLUGIN_TYPE = "essencial"

    def __init__(self):
        """Inicializa o plugin de sinais."""
        super().__init__()
        self.nome = "sinais_plugin"
        self.descricao = "Plugin para gerenciamento de sinais de trading"
        self._config = None
        self.cache_sinais = {}

    def inicializar(self, config):
        """
        Inicializa o plugin com as configurações fornecidas.

        Args:
            config: Objeto de configuração
        """
        if not self._config:  # Só inicializa uma vez
            super().inicializar(config)
            self._config = config
            self.cache_sinais = {}
            return True
        return True

    def executar(self, *args, **kwargs) -> bool:
        """
        Gera sinais de negociação com base nos indicadores processados.

        Args:
            *args: Argumentos posicionais (não utilizados diretamente).
            **kwargs: Argumentos nomeados, incluindo:
                - dados_completos (dict): Dicionário com dados brutos e processados.
                - symbol (str): O par de negociação (ex.: "BTCUSDT").
                - timeframe (str): O intervalo de tempo (ex.: "1m", "1d").

        Returns:
            bool: True se os sinais foram gerados e salvos com sucesso, False caso contrário.
        """
        dados_completos = kwargs.get("dados_completos")
        symbol = kwargs.get("symbol")
        timeframe = kwargs.get("timeframe")

        if not dados_completos or not symbol or not timeframe:
            logger.error("Parâmetros inválidos para sinais_plugin")
            return False

        tendencia = dados_completos["processados"].get(
            "tendencia", {"direcao": "NEUTRO", "forca": "FRACA", "confianca": 0.0}
        )
        medias_moveis = dados_completos["processados"].get("medias_moveis", {})

        sinal = {
            "direcao": tendencia["direcao"],  # Usa a tendência calculada
            "forca": "MÉDIA",
            "confianca": max(
                tendencia["confianca"], medias_moveis.get("confianca", 0.0)
            )
            / 2,
            "indicadores": {"tendencia": tendencia, "medias_moveis": medias_moveis},
        }

        logger.info(f"Sinais gerados para {symbol} ({timeframe}): {sinal}")
        dados_completos["processados"]["sinais"] = sinal
        return True

    def validar_dados(self, dados):
        """
        Valida se os dados dos indicadores são válidos.

        Args:
            dados (dict): Dicionário com os sinais dos indicadores

        Returns:
            bool: True se os dados são válidos, False caso contrário
        """
        try:
            if not dados or not isinstance(dados, dict):
                logger.error("Dados inválidos: não é um dicionário")
                return False

            indicadores_necessarios = ["tendencia", "medias_moveis"]
            if not any(ind in dados for ind in indicadores_necessarios):
                logger.warning("Nenhum indicador necessário encontrado")
                return True

            for indicador, resultado in dados.items():
                if not isinstance(resultado, dict):
                    logger.error(f"Resultado inválido para {indicador}")
                    continue

                if "direcao" not in resultado:
                    dados[indicador] = {
                        "direcao": "NEUTRO",
                        "forca": resultado.get("forca", "FRACA"),
                        "confianca": resultado.get("confianca", 0.0),
                    }

            return True

        except Exception as e:
            logger.error(f"Erro na validação dos dados: {e}")
            return False

    def validar_sinal(self, sinal):
        """
        Valida se o sinal consolidado é válido para ser enviado.

        Args:
            sinal (dict): Sinal consolidado

        Returns:
            bool: True se o sinal deve ser enviado, False caso contrário
        """
        try:
            campos_obrigatorios = ["direcao", "forca", "confianca"]
            if not all(campo in sinal for campo in campos_obrigatorios):
                return False

            if sinal["direcao"] == "NEUTRO" or sinal["forca"] == "FRACA":
                return False

            if sinal["confianca"] < 80:
                return False

            return True

        except Exception as e:
            logger.error(f"Erro na validação do sinal: {e}")
            return False

    def consolidar_sinais(self, dados):
        """
        Consolida os sinais de diferentes indicadores em um único sinal.

        Args:
            dados (dict): Dicionário com os sinais dos indicadores

        Returns:
            dict: Sinal consolidado com direção, força e confiança ou None em caso de erro
        """
        try:
            if dados is None or not self.validar_dados(dados):
                return None

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

            if "tendencia" in dados and "direcao" in dados["tendencia"]:
                peso = 3
                peso_total += peso
                if dados["tendencia"]["direcao"] == "ALTA":
                    sinais_alta += peso
                elif dados["tendencia"]["direcao"] == "BAIXA":
                    sinais_baixa += peso

            if "medias_moveis" in dados and "direcao" in dados["medias_moveis"]:
                peso = 2
                peso_total += peso
                if dados["medias_moveis"]["direcao"] == "ALTA":
                    sinais_alta += peso
                elif dados["medias_moveis"]["direcao"] == "BAIXA":
                    sinais_baixa += peso

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

            if "tendencia" in dados and "forca" in dados["tendencia"]:
                peso = 3
                peso_total += peso
                if dados["tendencia"]["forca"] == "FORTE":
                    forca_total += peso * 3
                elif dados["tendencia"]["forca"] == "MÉDIA":
                    forca_total += peso * 2
                elif dados["tendencia"]["forca"] == "FRACA":
                    forca_total += peso

            if "medias_moveis" in dados and "forca" in dados["medias_moveis"]:
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
                if forca_media >= 85:
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

            if "tendencia" in dados and "confianca" in dados["tendencia"]:
                peso = 3
                peso_total += peso
                confianca_total += dados["tendencia"]["confianca"] * peso

            if "medias_moveis" in dados and "confianca" in dados["medias_moveis"]:
                peso = 2
                peso_total += peso
                confianca_total += dados["medias_moveis"]["confianca"] * peso

            if peso_total > 0:
                return round(confianca_total / peso_total, 2)

            return 0.0

        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.0

    def logar_sinal(self, symbol, timeframe, sinal):
        """
        Loga um sinal de trading.

        Args:
            symbol (str): Símbolo do par
            timeframe (str): Timeframe do sinal
            sinal (dict): Dados do sinal

        Returns:
            dict: Sinal formatado e registrado
        """
        try:
            if not all([symbol, timeframe, sinal]):
                raise ValueError("Dados inválidos para logging de sinal")

            sinal_formatado = {
                "symbol": symbol,
                "timeframe": timeframe,
                "direcao": sinal.get("direcao"),
                "stop_loss": sinal.get("stop_loss"),
                "take_profit": sinal.get("take_profit"),
            }

            logger.info(f"Sinal registrado: {sinal_formatado}")
            return sinal_formatado

        except Exception as e:
            logger.error(f"Erro ao logar sinal: {e}")
            raise
