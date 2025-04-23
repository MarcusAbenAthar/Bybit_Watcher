"""
Plugin institucional para monitoramento criterioso de ordens/posições abertas.
Executa apenas se auto_trade estiver True no config.
- Frequência e ciclo definidos pelo pipeline.
- Modular, seguro, documentado e testável.
- Responsabilidade única: monitorar status, SL/TP, liquidação e alertas de ordens abertas.
"""

from plugins.plugin import Plugin
from utils.logging_config import get_logger
from utils.config import carregar_config

logger = get_logger(__name__, monitoramento=True)

class MonitorOrdens(Plugin):
    def finalizar(self):
        """
        Finaliza o plugin MonitorOrdens, limpando estado e garantindo shutdown seguro.
        """
        try:
            super().finalizar()
            logger.info("MonitorOrdens finalizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao finalizar MonitorOrdens: {e}")

    PLUGIN_NAME = "monitor_ordens"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["monitoramento", "ordens", "prioridade"]
    PLUGIN_PRIORIDADE = 120

    @classmethod
    def dependencias(cls):
        """
        Retorna lista de dependências obrigatórias.
        """
        return ["execucao_ordens", "conexao"]

    def __init__(self, execucao_ordens=None, conexao=None, **kwargs):
        """
        Inicializa o plugin MonitorOrdens.
        Args:
            execucao_ordens: Plugin de execução de ordens.
            conexao: Plugin de conexão com corretora.
        """
        super().__init__(**kwargs)
        self.execucao_ordens = execucao_ordens
        self.conexao = conexao
        self.config = kwargs.get("config") or carregar_config()

    def monitorar(self) -> dict:
        """
        Monitora todas as ordens/posições abertas, apenas se auto_trade=True.
        Retorna status e alertas institucionais.
        """
        try:
            auto_trade = self.config.get("trading", {}).get("auto_trade", False)
            if not auto_trade:
                logger.info("[MonitorOrdens] auto_trade está False. Monitoramento de ordens desativado.")
                return {"status": "INATIVO", "alerta": "Monitoramento desativado (auto_trade=False)"}

            ordens_ativas = self.execucao_ordens.listar_ordens_ativas() if self.execucao_ordens else []
            if not ordens_ativas:
                return {"status": "OK", "ordens": [], "alerta": None}

            alertas = []
            for ordem in ordens_ativas:
                # Exemplo institucional: checa status, SL/TP, liquidação
                status = ordem.get("status")
                sl = ordem.get("sl")
                tp = ordem.get("tp")
                preco_atual = self.conexao.obter_preco(ordem["symbol"]) if self.conexao else None
                alerta = None
                if status == "liquidada":
                    alerta = f"Ordem {ordem['id']} liquidada!"
                elif preco_atual is not None:
                    if sl and preco_atual <= sl:
                        alerta = f"Ordem {ordem['id']} atingiu SL!"
                    elif tp and preco_atual >= tp:
                        alerta = f"Ordem {ordem['id']} atingiu TP!"
                if alerta:
                    alertas.append(alerta)
            status_final = "ALERTA" if alertas else "OK"
            return {"status": status_final, "ordens": ordens_ativas, "alertas": alertas}
        except Exception as e:
            logger.error(f"[MonitorOrdens] Erro ao monitorar ordens: {e}")
            return {"status": "ERRO", "ordens": [], "alertas": [str(e)]}

    def diagnostico(self):
        """
        Interface padronizada para integração com pipeline.
        """
        return self.monitorar()
