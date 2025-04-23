"""
Plugin Sentinela: Diagnóstico Estratégico de Sentimento de Mercado

Integra sentimento fundamental (FGI, LSR, BTC.d) e técnico (RSI, ATR, volume, tendência BTC)
para orientar decisões automáticas de trading com segurança, clareza e modularidade.

- Responsabilidade única: diagnóstico de contexto e estratégia de risco.
- Modular, testável, documentado e sem hardcode.
- Autoidentificação de dependências/plugins.
"""
from plugins.plugin import Plugin
from utils.logging_config import get_logger
from utils.config import carregar_config
from plugins.gerenciadores.gerenciador_monitoramento import GerenciadorMonitoramento

logger = get_logger(__name__)

class Sentinela(...):
    def finalizar(self):
        """
        Finaliza o plugin Sentinela, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("Sentinela finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar Sentinela: {e}")

class Sentinela(Plugin):
    """
    Plugin Sentinela: Diagnóstico Estratégico de Sentimento de Mercado.

    Integra sentimento fundamental (FGI, LSR, BTC.d) e técnico (RSI, ATR, volume, tendência BTC)
    para orientar decisões automáticas de trading com segurança, clareza e modularidade.

    - Responsabilidade única: diagnóstico de contexto e estratégia de risco.
    - Modular, testável, documentado e sem hardcode.
    - Autoidentificação de dependências/plugins.
    """
    PLUGIN_NAME = "sentinela"
    PLUGIN_TYPE = "analise"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["sentinela", "estrategico", "sentimento", "confluencia"]
    PLUGIN_PRIORIDADE = 100

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de nomes das dependências obrigatórias do plugin Sentinela.
        """
        return [
            "obter_dados",  # Para FGI, LSR, BTC.d
            "indicadores_osciladores",  # RSI
            "indicadores_volatilidade",  # ATR
            "indicadores_tendencia",  # EMA/ADX
        ]


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = carregar_config()

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com configurações fornecidas.
        """
        self.config = config
        logger.info(f"[{self.PLUGIN_NAME}] Inicializado com config dinâmica.")
        return True

    def executar(self, dados_completos: dict, **kwargs) -> dict:
        """
        Executa o diagnóstico estratégico consolidando sentimento fundamental, técnico e monitoramento avançado (funding, open interest, onchain, etc).
        Integra diagnósticos do GerenciadorMonitoramento de forma modular, segura e padronizada.

        Args:
            dados_completos (dict): Dicionário compartilhado do pipeline do bot.
        Returns:
            dict: Diagnóstico estratégico consolidado, com status, resumo sintético, alertas, detalhes e monitoramento completo.
        """
        # --- Coleta dos módulos dependentes ---
        obter_dados = kwargs.get('obter_dados')
        osc = kwargs.get('indicadores_osciladores')
        vol = kwargs.get('indicadores_volatilidade')
        tend = kwargs.get('indicadores_tendencia')
        ativos = self.config.get('ATIVOS_SENTINELA', ['BTCUSDT','ETHUSDT'])

        # --- Sentimento Fundamental ---
        fgi = obter_dados.obter_fear_greed_index() if obter_dados else {}
        lsr = obter_dados.obter_long_short_ratio(ativos[0]) if obter_dados else {}
        btc_dom = obter_dados.obter_btc_dominance() if obter_dados else {}

        # --- Sentimento Técnico ---
        rsi_medios = []
        atr_medios = []
        volumes = []
        for symbol in ativos:
            rsi = osc.calcular_rsi(dados_completos.get(symbol, {}).get('crus', [])) if osc else []
            atr = vol.calcular_atr(dados_completos.get(symbol, {}).get('crus', [])) if vol else []
            volume = sum([c[5] for c in dados_completos.get(symbol, {}).get('crus', [])]) if dados_completos.get(symbol, {}).get('crus') else 0
            if len(rsi): rsi_medios.append(rsi[-1])
            if len(atr): atr_medios.append(atr[-1])
            volumes.append(volume)
        rsi_medio = sum(rsi_medios)/len(rsi_medios) if rsi_medios else None
        atr_medio = sum(atr_medios)/len(atr_medios) if atr_medios else None
        volume_total = sum(volumes)

        # Tendência BTC
        tendencia_btc = None
        if tend:
            cruzamento = tend.cruzamento_ema(dados_completos.get('BTCUSDT', {}).get('crus', []))
            tendencia_btc = cruzamento.get('direcao') if cruzamento else None

        # --- Diagnóstico Monitoramento Avançado ---
        monitoramento_resultados = {}
        try:
            ger_monitoramento = GerenciadorMonitoramento(config=self.config)
            ger_monitoramento.inicializar(config=self.config)
            monitoramento_resultados = ger_monitoramento.executar(symbol=ativos[0])  # Exemplo: executa para o ativo principal
        except Exception as e:
            logger.error(f"[Sentinela] Falha ao executar GerenciadorMonitoramento: {e}")

        # --- Detalhes brutos para debug e integração ---
        detalhes = {
            "rsi": rsi_medio,
            "atr": atr_medio,
            "volume_total": volume_total,
            "fgi_valor": fgi.get('value'),
            "lsr_valor": lsr.get('lsr'),
            "btc_dominance": btc_dom.get('dominance'),
            "btc_direcao": btc_dom.get('direcao'),
        }

        # --- Diagnóstico Estratégico ---
        contexto_risco = self._avaliar_contexto(fgi, lsr, rsi_medio, atr_medio, volume_total)
        alavancagem_sugerida = self._sugerir_alavancagem(contexto_risco)
        protecao_sugerida = self._sugerir_protecao(contexto_risco)
        classe_ativo_sugerida = self._sugerir_classe_ativo(btc_dom, tendencia_btc)

        # --- Alertas Estratégicos Inteligentes ---
        alertas = []
        if btc_dom.get('dominance', 0) > 50 and tendencia_btc == 'Alta':
            alertas.append("Alta dominância BTC + tendência de alta: altcoins podem underperformar.")
        if fgi.get('value', 50) < 20 and lsr.get('lsr', 1) > 2:
            alertas.append("FGI extremo de medo + LSR muito comprado: risco de squeeze de alta.")
        if atr_medio and atr_medio > self.config.get('ATR_ALTO', 200):
            alertas.append("Volatilidade muito alta: ajuste SL/TP e alavancagem recomendado.")
        if rsi_medio and (rsi_medio > 70 or rsi_medio < 30):
            alertas.append("RSI extremo: risco de reversão técnica.")
        if not fgi or not lsr or rsi_medio is None or atr_medio is None:
            alertas.append("Dados incompletos para diagnóstico total. Sinalize cautela!")
        # Incorpora alertas dos plugins de monitoramento
        for nome, diag in monitoramento_resultados.items():
            alerta = diag.get("alerta")
            if alerta:
                alertas.append(f"[{nome}] {alerta}")

        # --- Diagnóstico Sintético ---
        diagnostico_sintetico = f"RISCO {contexto_risco.upper()} | ALAVANCAGEM {alavancagem_sugerida} | PROTEÇÃO {protecao_sugerida.upper()} | FOCO: {classe_ativo_sugerida}"

        # --- Status e dados parciais ---
        dados_parciais = not (fgi and lsr and rsi_medio is not None and atr_medio is not None)
        status = "OK" if not dados_parciais else ("DADOS_INCOMPLETOS" if any([fgi, lsr, rsi_medio, atr_medio]) else "ERRO")

        resultado = {
            "status": status,
            "dados_parciais": dados_parciais,
            "diagnostico_sintetico": diagnostico_sintetico,
            "fgi_sentimento": fgi.get('classification'),
            "lsr_direcao": lsr.get('direcao'),
            "btc_direcao": btc_dom.get('direcao'),
            "btc_dominio": btc_dom.get('dominance'),
            "btc_categoria": btc_dom.get('categoria'),
            "sentimento_tecnico": self._avaliar_sentimento_tecnico(rsi_medio),
            "nivel_volatilidade": self._avaliar_volatilidade(atr_medio),
            "forca_tendencia_btc": tendencia_btc,
            "contexto_risco": contexto_risco,
            "alavancagem_sugerida": alavancagem_sugerida,
            "protecao_sugerida": protecao_sugerida,
            "classe_ativo_sugerida": classe_ativo_sugerida,
            "alertas_estrategicos": alertas,
            "detalhes": detalhes,
            "monitoramento": monitoramento_resultados,
        }
        logger.info(f"[{self.PLUGIN_NAME}] Diagnóstico estratégico: {resultado}")
        return resultado

    # --- Métodos auxiliares de decisão ---
    def _avaliar_contexto(self, fgi, lsr, rsi_medio, atr_medio, volume_total):
        """
        Avalia o contexto de risco do mercado combinando sentimento fundamental e técnico.
        """
        if not fgi or not lsr or rsi_medio is None or atr_medio is None:
            return "Indefinido"
        if fgi.get('value', 50) < 25 and lsr.get('lsr', 1) < 0.5 and rsi_medio < 30 and volume_total < self.config.get('VOLUME_BAIXO', 1e6):
            return "Baixo"
        if fgi.get('value', 50) > 75 and lsr.get('lsr', 1) > 3 and rsi_medio > 70 and volume_total > self.config.get('VOLUME_ALTO', 1e7):
            return "Alto"
        return "Moderado"

    def _sugerir_alavancagem(self, contexto):
        if contexto == "Baixo": return "1x-3x"
        if contexto == "Alto": return "0x"
        return "1x"

    def _sugerir_protecao(self, contexto):
        if contexto == "Alto": return "Hedge/Stop Curto"
        if contexto == "Baixo": return "Stop Curto"
        return "Gerenciamento Padrão"

    def _sugerir_classe_ativo(self, btc_dom, tendencia_btc):
        if btc_dom.get('dominance', 0) > 50 and btc_dom.get('direcao') == 'Subindo' and tendencia_btc == 'Alta':
            return "BTC"
        if btc_dom.get('dominance', 0) < 45 and btc_dom.get('direcao') == 'Caindo':
            return "Altcoins"
        return "BTC/Alts"

    def _avaliar_sentimento_tecnico(self, rsi):
        if rsi is None: return "Indefinido"
        if rsi > 70: return "Sobrecomprado"
        if rsi < 30: return "Sobrevendido"
        return "Neutro"

    def _avaliar_volatilidade(self, atr):
        if atr is None: return "Indefinido"
        if atr > self.config.get('ATR_ALTO', 200): return "Alta"
        if atr < self.config.get('ATR_BAIXO', 50): return "Baixa"
        return "Moderada"

    @classmethod
    def dependencias(cls):
        """Autoidentificação de dependências do plugin."""
        return cls.DEPENDENCIAS

    @classmethod
    def identificar_plugins(cls):
        """Autoidentificação do plugin Sentinela."""
        return cls.PLUGIN_NAME
