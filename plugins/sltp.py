"""
Plugin SLTP inteligente com adaptação dinâmica baseada em contexto, performance e confiança.
"""

from typing import Dict, Any, Optional
from plugins.plugin import Plugin
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SLTP(Plugin):
    """
    Plugin para cálculo inteligente de Stop Loss (SL) e Take Profit (TP), com lógica adaptativa.
    - Responsabilidade única: cálculo de SL/TP.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """

    PLUGIN_NAME = "sltp"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sltp", "gerenciamento", "risco"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin SLTP.
        """
        return ["calculo_risco", "calculo_alavancagem"]

    PLUGIN_NAME = "sltp"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["gerador", "sinal", "sltp"]
    PLUGIN_PRIORIDADE = 90

    def __init__(self, **kwargs):
        """
        Inicializa o plugin SLTP.

        Args:
            **kwargs: Dependências injetadas.
        """
        super().__init__(**kwargs)
        self._historico_resultados = []
        self._estilos_sltp = {}
        self._max_historico = 100  # Limite para histórico em memória

    def inicializar(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa o plugin com configurações.

        Args:
            config: Dicionário com configurações.

        Returns:
            bool: True se inicializado, False caso contrário.
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            self._estilos_sltp = self._carregar_estilos(config)
            if not self._estilos_sltp:
                logger.error(f"[{self.nome}] Nenhum estilo SL/TP válido carregado")
                return False

            logger.info(
                f"[{self.nome}] Inicializado com estilos: {list(self._estilos_sltp.keys())}"
            )
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}", exc_info=True)
            return False

    def _carregar_estilos(self, config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Carrega estilos SL/TP da configuração.

        Args:
            config: Dicionário com configurações.

        Returns:
            dict: Estilos SL/TP válidos.
        """
        try:
            estilos = config.get("sltp_estilos", {})
            estilos_padrao = {
                "conservador": {"sl_mult": 0.5, "tp_mult": 1.0},
                "moderado": {"sl_mult": 1.0, "tp_mult": 1.5},
                "agressivo": {"sl_mult": 1.5, "tp_mult": 3.0},
            }

            if not isinstance(estilos, dict) or not estilos:
                logger.warning(
                    f"[{self.nome}] Estilos SL/TP não encontrados. Usando padrão."
                )
                return estilos_padrao

            estilos_validados = {}
            for nome, params in estilos.items():
                if not isinstance(params, dict):
                    logger.warning(f"[{self.nome}] Estilo {nome} inválido: {params}")
                    continue
                sl_mult = params.get("sl_mult")
                tp_mult = params.get("tp_mult")
                if (
                    isinstance(sl_mult, (int, float))
                    and isinstance(tp_mult, (int, float))
                    and sl_mult > 0
                    and tp_mult > 0
                ):
                    estilos_validados[nome] = {"sl_mult": sl_mult, "tp_mult": tp_mult}
                else:
                    logger.warning(
                        f"[{self.nome}] Parâmetros inválidos para {nome}: {params}"
                    )
            if not estilos_validados:
                logger.warning(f"[{self.nome}] Nenhum estilo válido. Usando padrão.")
                return estilos_padrao

            logger.info(
                f"[{self.nome}] Estilos SL/TP carregados: {list(estilos_validados.keys())}"
            )
            return estilos_validados
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao carregar estilos: {e}")
            return {"moderado": {"sl_mult": 1.0, "tp_mult": 1.5}}

    def _get_estilo_padrao(self) -> str:
        """
        Retorna o estilo padrão.

        Returns:
            str: Nome do estilo padrão.
        """
        try:
            estilo = self._config.get("sltp_estilo_padrao", "moderado")
            if estilo in self._estilos_sltp:
                return estilo
            logger.warning(
                f"[{self.nome}] Estilo padrão {estilo} não encontrado. Usando primeiro disponível."
            )
            return next(iter(self._estilos_sltp), "moderado")
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao obter estilo padrão: {e}")
            return "moderado"

    def _simular_cenarios(
        self, atr: float, candle_tamanho: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Simula cenários SL/TP para cada estilo.

        Args:
            atr: Valor do ATR.
            candle_tamanho: Tamanho da candle.

        Returns:
            dict: Cenários SL/TP por estilo.
        """
        try:
            if not isinstance(atr, (int, float)) or atr <= 0:
                logger.error(f"[{self.nome}] ATR inválido: {atr}")
                return {}
            return {
                estilo: {
                    "sl": round(atr * params.get("sl_mult", 1.0), 4),
                    "tp": round(atr * params.get("tp_mult", 1.5), 4),
                }
                for estilo, params in self._estilos_sltp.items()
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na simulação de SL/TP: {e}")
            return {}

    def _ajustar_por_performance(self) -> str:
        """
        Ajusta o estilo com base na performance histórica.

        Returns:
            str: Estilo ajustado.
        """
        try:
            if not self._historico_resultados:
                return self._get_estilo_padrao()

            ultimos = self._historico_resultados[-5:]
            acertos = sum(1 for r in ultimos if r["resultado"] == "TP")
            erros = sum(1 for r in ultimos if r["resultado"] == "SL")

            if acertos >= 4 and "agressivo" in self._estilos_sltp:
                return "agressivo"
            if erros >= 3 and "conservador" in self._estilos_sltp:
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na avaliação de performance: {e}")
            return self._get_estilo_padrao()

    def _contexto_multitemporal(
        self, contexto: Dict[str, Any], direcao: str, forca: str
    ) -> str:
        """
        Avalia o contexto multitemporal para selecionar estilo.

        Args:
            contexto: Dados de contexto.
            direcao: Direção do sinal.
            forca: Força do sinal.

        Returns:
            str: Estilo selecionado.
        """
        try:
            tendencia_macro = contexto.get("tendencia_macro", "LATERAL")
            # Compatibilidade com "NEUTRO" da versão original
            if tendencia_macro == "NEUTRO":
                tendencia_macro = "LATERAL"
            if tendencia_macro != direcao or forca == "LATERAL":
                return "conservador"
            return self._get_estilo_padrao()
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na avaliação de contexto: {e}")
            return self._get_estilo_padrao()

    def _consolidar_com_indicadores(
        self,
        sl: float,
        tp: float,
        contexto: Dict[str, Any],
        direcao: str,
        preco_atual: float,
    ) -> Dict[str, float]:
        """
        Ajusta SL/TP com base em indicadores e direção.

        Args:
            sl: Stop-loss bruto.
            tp: Take-profit bruto.
            contexto: Dados de contexto.
            direcao: Direção do sinal.
            preco_atual: Preço atual do ativo.

        Returns:
            dict: SL/TP ajustados.
        """
        try:
            mm_barreira = contexto.get("ma_resistencia", 0.0)
            sl_ajustado = max(sl, mm_barreira * 0.05) if mm_barreira > 0 else sl

            # Ajustar SL/TP com base na direção
            if direcao == "ALTA":
                stop_loss = preco_atual - sl_ajustado
                take_profit = preco_atual + tp
            elif direcao == "BAIXA":
                stop_loss = preco_atual + sl_ajustado
                take_profit = preco_atual - tp
            else:
                stop_loss = preco_atual - sl_ajustado  # Padrão conservador
                take_profit = preco_atual + tp

            return {
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
            }
        except Exception as e:
            logger.error(f"[{self.nome}] Erro na consolidação com indicadores: {e}")
            return {
                "stop_loss": round(preco_atual - sl, 2),
                "take_profit": round(preco_atual + tp, 2),
            }

    def _registrar_resultado(self, sinal: Dict[str, Any], resultado: str):
        """
        Registra o resultado do sinal no histórico.

        Args:
            sinal: Dados do sinal.
            resultado: Resultado ("TP", "SL", "nenhum").
        """
        try:
            registro = {
                "direcao": sinal.get("direcao"),
                "sl": sinal.get("stop_loss"),
                "tp": sinal.get("take_profit"),
                "indicadores": sinal.get("indicadores_ativos", []),
                "resultado": resultado,
            }
            self._historico_resultados.append(registro)
            if len(self._historico_resultados) > self._max_historico:
                self._historico_resultados.pop(0)
            # TODO: Integrar com banco_dados.py quando implementado
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao registrar resultado: {e}")

    def executar(self, *args, **kwargs):
        resultado_padrao = {
            "sltp": {"stop_loss": None, "take_profit": None, "confianca": 0.0}
        }
        try:
            dados_completos = kwargs.get("dados_completos")
            symbol = kwargs.get("symbol")
            timeframe = kwargs.get("timeframe")
            if not all([dados_completos, symbol, timeframe]):
                logger.error(f"[{self.nome}] Parâmetros obrigatórios ausentes")
                return resultado_padrao
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                return resultado_padrao
            candles = dados_completos.get("crus", [])
            if not self._validar_candles(candles, symbol, timeframe):
                return resultado_padrao
            resultado = self._calcular_sltp(candles)
            logger.debug(f"[{self.nome}] SL/TP para {symbol}-{timeframe}: {resultado}")
            return {"sltp": resultado}
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}", exc_info=True)
            return resultado_padrao

    def finalizar(self):
        """
        Finaliza o plugin SLTP, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.debug("SLTP finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar SLTP: {e}")

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "sltp": {
                "descricao": "Armazena cálculos de SL/TP, score, contexto, observações e candle para rastreabilidade e auditoria.",
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "stop_loss": "DECIMAL(18,8)",
                    "take_profit": "DECIMAL(18,8)",
                    "confianca": "DECIMAL(5,2)",
                    "score": "DECIMAL(5,2)",
                    "contexto_mercado": "VARCHAR(20)",
                    "observacoes": "TEXT",
                    "candle": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            }
        }

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"
