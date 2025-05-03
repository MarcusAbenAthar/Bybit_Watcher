"""Plugin para consolidação de sinais de múltiplos timeframes."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from utils.logging_config import get_logger
from plugins.plugin import Plugin
import time
import hashlib
import datetime

logger = get_logger(__name__)


@dataclass
class SinalTimeframe:
    """Estrutura para armazenar sinal de um timeframe específico."""

    timeframe: str
    direcao: str
    forca: str
    confianca: float
    preco_atual: float
    suporte: float
    resistencia: float
    atr: float
    volume: float = 0.0
    rsi: float = 0.0
    tendencia: str = "LATERAL"


@dataclass
class SinalConsolidado:
    """Estrutura para armazenar o sinal consolidado."""

    direcao: str
    faixa_entrada: Tuple[float, float]
    tp1: float
    tp2: float
    sl: float
    alavancagem: int
    confianca: float
    volume_rel: float = 0.0
    forca: str = "FRACA"


class ConsolidadorSinais(Plugin):
    """
    Plugin para consolidação de sinais de múltiplos timeframes.
    - Responsabilidade única: consolidar sinais em um único sinal acionável
    - Modular e configurável
    - Documentado e testável
    """

    PLUGIN_NAME = "consolidador_sinais"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sinais", "consolidacao", "analise"]
    PLUGIN_PRIORIDADE = 90

    # Schema da tabela
    PLUGIN_TABELAS = {
        "sinais_consolidados": {
            "schema": {
                "id": "SERIAL PRIMARY KEY",
                "timestamp": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "symbol": "VARCHAR(20) NOT NULL",
                "direcao": "VARCHAR(10) NOT NULL",
                "entrada_min": "DECIMAL(18,8) NOT NULL",
                "entrada_max": "DECIMAL(18,8) NOT NULL",
                "tp1": "DECIMAL(18,8) NOT NULL",
                "tp2": "DECIMAL(18,8) NOT NULL",
                "sl": "DECIMAL(18,8) NOT NULL",
                "alavancagem": "INTEGER NOT NULL",
                "confianca": "DECIMAL(5,2) NOT NULL",
                "timeframes_concordantes": "INTEGER NOT NULL",
                "diff_pontuacao": "DECIMAL(5,2) NOT NULL",
                "forca": "VARCHAR(10) NOT NULL",
                "volume_rel": "DECIMAL(10,2) NOT NULL",
                "rsi": "DECIMAL(5,2)",
                "tendencia": "VARCHAR(10)",
                "ultima_atualizacao": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
            "modo_acesso": "write",
            "dependencias": ["banco_dados"],
        }
    }

    # Pesos dos timeframes
    PESOS_TIMEFRAMES = {"4h": 0.40, "1h": 0.30, "30m": 0.20, "15m": 0.10}

    # Thresholds de confiança
    CONFIANCA_MIN = 45.0  # Aumentado de 35 para 45
    DIFF_PONTUACAO_MIN = 25.0  # Aumentado de 20 para 25

    # Multiplicadores para SL/TP baseados no ATR
    SL_ATR_MULT = 1.5
    TP1_ATR_MULT = 2.0
    TP2_ATR_MULT = 3.5

    def __init__(self, gerente=None, **kwargs):
        """Inicializa o ConsolidadorSinais."""
        super().__init__(**kwargs)
        self._sinais: Dict[str, SinalTimeframe] = {}
        self._ultimo_sinal = {}  # Cache para evitar duplicação
        self._contador_sinais = {}  # Contador para controle de frequência
        self._gerente = gerente  # Gerente de plugins, pode ser setado no construtor

    def set_gerente(self, gerente):
        """Define o gerente de plugins para acesso a dependências."""
        self._gerente = gerente

    def _calcular_pontuacao_direcao(self) -> Dict[str, float]:
        """Calcula a pontuação ponderada para cada direção."""
        pontuacao = {"LONG": 0.0, "SHORT": 0.0}
        volume_total = 0.0

        for tf, sinal in self._sinais.items():
            peso = self.PESOS_TIMEFRAMES[tf]
            # Incorpora volume e RSI na pontuação
            volume_rel = sinal.volume if hasattr(sinal, "volume") else 1.0
            rsi_factor = self._calcular_rsi_factor(
                sinal.rsi if hasattr(sinal, "rsi") else 50
            )

            pontuacao[sinal.direcao] += (
                peso * (sinal.confianca / 100) * volume_rel * rsi_factor
            )
            volume_total += volume_rel

        # Normalização por volume
        if volume_total > 0:
            for dir in pontuacao:
                pontuacao[dir] = pontuacao[dir] / volume_total

        return pontuacao

    def _calcular_rsi_factor(self, rsi: float) -> float:
        """Calcula fator de ajuste baseado no RSI."""
        if rsi >= 70:
            return 0.7  # Sobrecomprado
        elif rsi <= 30:
            return 1.3  # Sobrevendido
        return 1.0

    def _determinar_direcao(self) -> Tuple[str, float]:
        """
        Determina a direção final com base nas pontuações.
        Returns:
            Tuple[str, float]: (direção, diferença percentual entre pontuações)
        """
        pontuacao = self._calcular_pontuacao_direcao()

        # Verifica tendência predominante
        tendencias = [s.tendencia for s in self._sinais.values()]
        tendencia_predominante = max(set(tendencias), key=tendencias.count)

        if pontuacao["LONG"] > pontuacao["SHORT"]:
            diff = (
                (pontuacao["LONG"] - pontuacao["SHORT"]) / max(pontuacao["SHORT"], 0.01)
            ) * 100
            # Ajusta baseado na tendência
            if (
                tendencia_predominante == "BAIXA"
                and diff < self.DIFF_PONTUACAO_MIN * 1.5
            ):
                return "LATERAL", diff
            return "LONG", diff
        else:
            diff = (
                (pontuacao["SHORT"] - pontuacao["LONG"]) / max(pontuacao["LONG"], 0.01)
            ) * 100
            # Ajusta baseado na tendência
            if (
                tendencia_predominante == "ALTA"
                and diff < self.DIFF_PONTUACAO_MIN * 1.5
            ):
                return "LATERAL", diff
            return "SHORT", diff

    def _calcular_faixa_entrada(self, direcao: str) -> Tuple[float, float]:
        """Calcula a faixa de entrada com base na direção e níveis técnicos."""
        sinal_4h = self._sinais.get("4h")
        if not sinal_4h:
            return (0.0, 0.0)

        preco_atual = sinal_4h.preco_atual
        atr = sinal_4h.atr

        # Ajuste dinâmico baseado na volatilidade
        volatilidade_factor = min(max(atr / preco_atual, 0.001), 0.05)

        if direcao == "LONG":
            suporte = sinal_4h.suporte
            entrada_min = max(suporte, preco_atual - atr * volatilidade_factor * 10)
            entrada_max = preco_atual + atr * volatilidade_factor * 4
        else:
            resistencia = sinal_4h.resistencia
            entrada_min = preco_atual - atr * volatilidade_factor * 4
            entrada_max = min(resistencia, preco_atual + atr * volatilidade_factor * 10)

        return (round(entrada_min, 8), round(entrada_max, 8))

    def _calcular_tp_sl(
        self, direcao: str, faixa_entrada: Tuple[float, float]
    ) -> Tuple[float, float, float]:
        """Calcula TP1, TP2 e SL com base na direção e faixa de entrada."""
        sinal_4h = self._sinais.get("4h")
        if not sinal_4h:
            return (0.0, 0.0, 0.0)

        entrada_media = (faixa_entrada[0] + faixa_entrada[1]) / 2
        atr = sinal_4h.atr

        # Ajuste dinâmico baseado na volatilidade
        volatilidade_factor = min(max(atr / entrada_media, 0.001), 0.05)

        if direcao == "LONG":
            sl = round(
                faixa_entrada[0] - atr * self.SL_ATR_MULT * volatilidade_factor, 8
            )
            tp1 = round(
                entrada_media + atr * self.TP1_ATR_MULT * volatilidade_factor, 8
            )
            tp2 = round(
                entrada_media + atr * self.TP2_ATR_MULT * volatilidade_factor, 8
            )
        else:
            sl = round(
                faixa_entrada[1] + atr * self.SL_ATR_MULT * volatilidade_factor, 8
            )
            tp1 = round(
                entrada_media - atr * self.TP1_ATR_MULT * volatilidade_factor, 8
            )
            tp2 = round(
                entrada_media - atr * self.TP2_ATR_MULT * volatilidade_factor, 8
            )

        return (tp1, tp2, sl)

    def _calcular_alavancagem(self, confianca: float, volume_rel: float) -> int:
        """Determina a alavancagem com base na confiança e volume relativo."""
        # Base inicial baseada na confiança
        if confianca >= 75:
            base = 10
        elif confianca >= 60:
            base = 7
        elif confianca >= 45:
            base = 5
        else:
            base = 3

        # Ajuste pelo volume relativo
        if volume_rel >= 2.0:  # Volume muito alto
            base = max(3, base - 2)
        elif volume_rel <= 0.5:  # Volume muito baixo
            base = max(3, base - 1)

        return base

    def _calcular_forca_sinal(
        self, confianca: float, volume_rel: float, concordantes: int
    ) -> str:
        """Calcula a força do sinal baseado em múltiplos fatores."""
        pontos = 0

        # Pontos por confiança
        if confianca >= 75:
            pontos += 3
        elif confianca >= 60:
            pontos += 2
        elif confianca >= 45:
            pontos += 1

        # Pontos por volume
        if volume_rel >= 2.0:
            pontos += 2
        elif volume_rel >= 1.5:
            pontos += 1

        # Pontos por concordância
        if concordantes >= 3:
            pontos += 2
        elif concordantes >= 2:
            pontos += 1

        # Determina força
        if pontos >= 6:
            return "FORTE"
        elif pontos >= 4:
            return "MÉDIA"
        return "FRACA"

    def _calcular_confianca_final(self, direcao: str) -> Tuple[float, int, float]:
        """
        Calcula a confiança consolidada.
        Returns:
            Tuple[float, int, float]: (confiança, timeframes concordantes, volume relativo médio)
        """
        confianca_base = 0.0
        concordantes = 0
        volume_total = 0.0
        volume_rel_medio = 0.0
        count = 0

        for tf, sinal in self._sinais.items():
            peso = self.PESOS_TIMEFRAMES[tf]
            volume_rel = getattr(sinal, "volume", 1.0)

            # Ajuste de confiança por RSI
            rsi_factor = self._calcular_rsi_factor(getattr(sinal, "rsi", 50))

            confianca_base += peso * sinal.confianca * rsi_factor
            volume_total += volume_rel

            if sinal.direcao == direcao:
                concordantes += 1

            count += 1

        # Cálculo do volume relativo médio
        volume_rel_medio = volume_total / count if count > 0 else 1.0

        # Ajustes na confiança
        if concordantes >= 3:
            confianca_base *= 1.2  # +20%
        elif concordantes <= 1:
            confianca_base *= 0.8  # -20%

        # Ajuste por volume
        if volume_rel_medio >= 2.0:
            confianca_base *= 1.1  # +10%
        elif volume_rel_medio <= 0.5:
            confianca_base *= 0.9  # -10%

        return round(confianca_base, 2), concordantes, volume_rel_medio

    def consolidar_sinais(self, sinais: Dict[str, SinalTimeframe]) -> Optional[str]:
        """
        Consolida os sinais em um único sinal acionável.

        Args:
            sinais: Dicionário de sinais por timeframe

        Returns:
            str: Sinal formatado ou None se não houver sinal claro
        """
        self._sinais = sinais

        # Validação inicial dos sinais
        if not self._validar_sinais():
            return None

        # 1. Determinar direção
        direcao, diff_pontuacao = self._determinar_direcao()
        if diff_pontuacao < self.DIFF_PONTUACAO_MIN:
            logger.info(f"Diferença de pontuação insuficiente: {diff_pontuacao:.2f}%")
            return None

        # 2. Calcular confiança
        confianca, concordantes, volume_rel_medio = self._calcular_confianca_final(
            direcao
        )
        if confianca < self.CONFIANCA_MIN:
            logger.info(f"Confiança insuficiente: {confianca:.2f}%")
            return None

        # 3. Calcular faixa de entrada
        faixa_entrada = self._calcular_faixa_entrada(direcao)
        if 0.0 in faixa_entrada:
            logger.error("Erro ao calcular faixa de entrada")
            return None

        # 4. Calcular TP e SL
        tp1, tp2, sl = self._calcular_tp_sl(direcao, faixa_entrada)
        if 0.0 in (tp1, tp2, sl):
            logger.error("Erro ao calcular TP/SL")
            return None

        # 5. Determinar alavancagem
        alavancagem = self._calcular_alavancagem(confianca, volume_rel_medio)

        # 6. Determinar força do sinal
        forca = self._calcular_forca_sinal(confianca, volume_rel_medio, concordantes)

        # 7. Verificar duplicação de sinal
        sinal_hash = self._gerar_hash_sinal(
            direcao, faixa_entrada, tp1, tp2, sl, alavancagem, confianca
        )
        if not self._verificar_novo_sinal(sinal_hash):
            logger.info("Sinal duplicado detectado, ignorando")
            return None

        # 8. Formatar sinal
        sinal = (
            f"XRPUSDT: {direcao}, "
            f"Entry {faixa_entrada[0]:.8f} ~ {faixa_entrada[1]:.8f}, "
            f"TP1: {tp1:.8f}, TP2: {tp2:.8f}, SL: {sl:.8f}, "
            f"Alavancagem: {alavancagem}x, "
            f"Confiança: {confianca:.2f}%, "
            f"Força: {forca}, "
            f"Volume Relativo: {volume_rel_medio:.2f}"
        )

        return sinal

    def _validar_sinais(self) -> bool:
        """Valida os sinais recebidos."""
        if not self._sinais:
            logger.warning("Nenhum sinal recebido")
            return False

        timeframes_necessarios = {"4h", "1h"}  # Mínimo necessário
        timeframes_recebidos = set(self._sinais.keys())

        if not timeframes_necessarios.issubset(timeframes_recebidos):
            logger.warning(
                f"Timeframes necessários ausentes. Recebidos: {timeframes_recebidos}"
            )
            return False

        for tf, sinal in self._sinais.items():
            if not all([sinal.preco_atual, sinal.atr]):
                logger.warning(f"Dados incompletos para {tf}")
                return False

        return True

    def _gerar_hash_sinal(self, *args) -> str:
        """Gera um hash único para o sinal."""
        return hashlib.md5(str(args).encode()).hexdigest()

    def _verificar_novo_sinal(self, sinal_hash: str) -> bool:
        """Verifica se o sinal é novo ou duplicado."""
        agora = time.time()

        # Limpar sinais antigos (mais de 5 minutos)
        self._ultimo_sinal = {
            k: v for k, v in self._ultimo_sinal.items() if agora - v < 300
        }

        if sinal_hash in self._ultimo_sinal:
            return False

        self._ultimo_sinal[sinal_hash] = agora
        return True

    def executar(self, *args, **kwargs):
        if self._gerente is None:
            # Tenta usar o atributo 'gerente' herdado da base Plugin
            if hasattr(self, 'gerente') and self.gerente is not None:
                self._gerente = self.gerente
            else:
                raise RuntimeError(f"[{self.nome}] Gerente de plugins não definido. Use set_gerente(gerente) ou passe gerente no construtor.")
        symbol = kwargs.get("symbol")
        dados = kwargs.get("dados_completos", {})

        # Adicionando validação para campos obrigatórios
        if not symbol:
            logger.error(f"[{self.nome}] Symbol não fornecido")
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
                "stop_loss": 0.0,
                "take_profit": 0.0,
            }

        # Garantir que `dados_crus` seja fornecido
        if not dados.get("crus"):
            logger.warning(f"[{self.nome}] Dados crus ausentes para {symbol}")
            dados["crus"] = self._gerente.obter_plugin("obter_dados").executar(
                symbol=symbol, timeframe=kwargs.get("timeframe", "1h")
            )

        # Garantir que `calculo_risco` seja integrado corretamente
        if "calculo_risco" not in dados or not dados["calculo_risco"]:
            logger.warning(
                f"[{self.nome}] Nenhum sinal válido encontrado para {symbol} (faltando: ['calculo_risco'])"
            )
            # Integrar cálculo de risco do plugin correspondente
            calculo_risco_plugin = self._gerente.obter_plugin("calculo_risco")
            if calculo_risco_plugin:
                dados["calculo_risco"] = calculo_risco_plugin.executar(
                    symbol=symbol,
                    timeframe=kwargs.get("timeframe", "1h"),
                    dados_completos=dados,
                )
            else:
                dados["calculo_risco"] = {"confianca": 0.0, "direcao": "LATERAL"}

        faltando = []
        for campo in ["crus", "candles", "alavancagem", "calculo_risco"]:
            if campo not in dados or not dados[campo]:
                faltando.append(campo)
                logger.debug(
                    f"[{self.nome}] Sem dados de análise de mercado para {symbol} - {campo}"
                )
        if faltando:
            logger.warning(
                f"[{self.nome}] Nenhum sinal válido encontrado para {symbol} (faltando: {faltando})"
            )
            # Retorna sinal padrão para não quebrar pipeline
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
                "stop_loss": 0.0,
                "take_profit": 0.0,
            }
        try:
            # Processar sinais de cada timeframe
            sinais = {}
            for tf, dados_tf in dados.items():
                dados_tf = self.normalizar_dados_tf(dados_tf)
                analise_mercado = dados_tf.get("analise_mercado", {})
                if not analise_mercado:
                    logger.debug(
                        f"[{self.nome}] Sem dados de análise de mercado para {symbol} - {tf}"
                    )
                    continue

                # Criar sinal para o timeframe
                try:
                    sinal = SinalTimeframe(
                        timeframe=tf,
                        direcao=analise_mercado.get("direcao", "LATERAL"),
                        forca=analise_mercado.get("forca", "FRACA"),
                        confianca=float(analise_mercado.get("confianca", 0.0)),
                        preco_atual=float(analise_mercado.get("preco_atual", 0.0)),
                        suporte=float(analise_mercado.get("suporte", 0.0)),
                        resistencia=float(analise_mercado.get("resistencia", 0.0)),
                        atr=float(analise_mercado.get("atr", 0.0)),
                        volume=float(analise_mercado.get("volume", 0.0)),
                        rsi=float(analise_mercado.get("rsi", 50.0)),
                        tendencia=analise_mercado.get("tendencia", "LATERAL"),
                    )
                    sinais[tf] = sinal
                except (ValueError, TypeError) as e:
                    logger.error(f"[{self.nome}] Erro ao criar sinal para {tf}: {e}")
                    continue

            if not sinais:
                logger.warning(
                    f"[{self.nome}] Nenhum sinal válido encontrado para {symbol}"
                )
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": None,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            # Consolidar sinais
            sinal_final = self.consolidar_sinais(sinais)
            if not sinal_final:
                logger.info(f"[{self.nome}] Sem sinal consolidado para {symbol}")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": None,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            if sinal_final.startswith("Sem sinal"):
                logger.info(f"[{self.nome}] {sinal_final}")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": None,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            # Salvar no banco de dados
            try:
                self._salvar_sinal_banco(symbol, sinal_final, sinais)
                logger.info(f"[{self.nome}] Sinal salvo com sucesso: {sinal_final}")
            except Exception as e:
                logger.error(f"[{self.nome}] Erro ao salvar sinal: {e}")
                return {
                    "direcao": "LATERAL",
                    "forca": "FRACA",
                    "confianca": 0.0,
                    "alavancagem": 0.0,
                    "timestamp": None,
                    "stop_loss": 0.0,
                    "take_profit": 0.0,
                }

            return {
                "direcao": sinal_final.split(", ")[0].split(": ")[1],
                "forca": sinal_final.split(", ")[7].split(": ")[1],
                "confianca": float(
                    sinal_final.split(", ")[6].split(": ")[1].rstrip("%")
                ),
                "alavancagem": int(
                    sinal_final.split(", ")[5].split(": ")[1].rstrip("x")
                ),
                "timestamp": datetime.datetime.now().isoformat(),
                "stop_loss": float(sinal_final.split(", ")[4].split(": ")[1]),
                "take_profit": float(sinal_final.split(", ")[3].split(": ")[1]),
            }

        except Exception as e:
            logger.error(f"[{self.nome}] Erro na execução: {e}", exc_info=True)
            return {
                "direcao": "LATERAL",
                "forca": "FRACA",
                "confianca": 0.0,
                "alavancagem": 0.0,
                "timestamp": None,
                "stop_loss": 0.0,
                "take_profit": 0.0,
            }

    def _salvar_sinal_banco(
        self, symbol: str, sinal_final: str, sinais: Dict[str, SinalTimeframe]
    ) -> None:
        """Salva o sinal consolidado no banco de dados."""
        banco_dados = self._gerente.obter_plugin("banco_dados")
        if not banco_dados:
            raise RuntimeError("Plugin banco_dados não encontrado")

        # Extrair valores do sinal
        partes = sinal_final.split(", ")
        direcao = partes[0].split(": ")[1]
        entrada = partes[1].split(": ")[1].split(" ~ ")
        entrada_min = float(entrada[0])
        entrada_max = float(entrada[1])
        tp1 = float(partes[2].split(": ")[1])
        tp2 = float(partes[3].split(": ")[1])
        sl = float(partes[4].split(": ")[1])
        alavancagem = int(partes[5].split(": ")[1].rstrip("x"))
        confianca = float(partes[6].split(": ")[1].rstrip("%"))
        forca = partes[7].split(": ")[1]
        volume_rel = float(partes[8].split(": ")[1])

        # Contar timeframes concordantes
        concordantes = sum(1 for s in sinais.values() if s.direcao == direcao)

        # Calcular diferença de pontuação
        pontuacao = self._calcular_pontuacao_direcao()
        diff_pontuacao = abs(pontuacao["LONG"] - pontuacao["SHORT"]) * 100

        dados = {
            "symbol": symbol,
            "direcao": direcao,
            "entrada_min": entrada_min,
            "entrada_max": entrada_max,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "alavancagem": alavancagem,
            "confianca": confianca,
            "timeframes_concordantes": concordantes,
            "diff_pontuacao": round(diff_pontuacao, 2),
            "forca": forca,
            "volume_rel": round(volume_rel, 2),
            "rsi": sinais["4h"].rsi if "4h" in sinais else 50.0,
            "tendencia": sinais["4h"].tendencia if "4h" in sinais else "LATERAL",
            "ultima_atualizacao": datetime.datetime.now().isoformat(),
        }

        banco_dados.inserir("sinais_consolidados", dados)

    def normalizar_dados_tf(self, dados_tf):
        # Se for dict, retorna direto (exceto se for só metadados)
        if isinstance(dados_tf, dict):
            # Remove metadados conhecidos
            metadados = {"symbol", "timeframe"}
            dados_filtrados = {k: v for k, v in dados_tf.items() if k not in metadados}
            if dados_filtrados:
                return dados_filtrados
            return dados_tf
        elif isinstance(dados_tf, list):
            # Se a lista contém inteiros, converte para string de timeframe
            if all(isinstance(x, int) for x in dados_tf):
                return {"dados": [f"{x}m" for x in dados_tf]}
            return {"dados": dados_tf}
        elif isinstance(dados_tf, int):
            # Converte int para string de timeframe
            return {"timeframe": f"{dados_tf}m"}
        # Se for str ou float e for metadado, ignore sem logar erro
        elif isinstance(dados_tf, (str, float)):
            return {}
        else:
            logger.error(
                f"[normalizar_dados_tf] Tipo inesperado: {type(dados_tf)} - valor: {dados_tf}"
            )
            return {}
