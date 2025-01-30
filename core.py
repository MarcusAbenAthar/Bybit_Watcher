# core.py
import configparser
import os
from datetime import datetime
from plugins.banco_dados import BancoDados  # Importa a classe BancoDados


class Core:
    def __init__(self):
        self.carregar_configuracoes()
        self.conectar_banco_dados()
        self.armazenar_logs()

    def carregar_configuracoes(self):
        """Carrega as configurações do arquivo config.ini."""
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

        self.bybit_api_key = self.config.get("Bybit", "API_KEY")
        self.bybit_api_secret = self.config.get("Bybit", "API_SECRET")
        self.nivel_alavancagem = self.config.getint("Geral", "NIVEL_ALAVANCAGEM")
        self.ativo = self.config.get("Geral", "ATIVO")

    def conectar_banco_dados(self):
        """Conecta ao banco de dados usando o plugin banco_dados.py."""
        self.banco_dados = BancoDados()  # Cria uma instância da classe BancoDados

    def armazenar_logs(self):
        """Configura o sistema de logs."""
        self.data_atual = datetime.now().strftime("%d%m%Y")
        self.nome_arquivo_log = f"bot{self.data_atual}.log"
        self.caminho_arquivo_log = os.path.join(
            os.path.dirname(__file__), "..", "logs", self.nome_arquivo_log
        )

        if not os.path.exists(self.caminho_arquivo_log):
            open(self.caminho_arquivo_log, "w").close()

        print(f"Logs serão armazenados em: {self.caminho_arquivo_log}")

    def registrar_log(self, mensagem):
        """Registra uma mensagem no arquivo de log."""
        try:
            with open(self.caminho_arquivo_log, "a") as arquivo_log:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                arquivo_log.write(f"{timestamp}: {mensagem}\n")
        except Exception as e:
            print(f"Erro ao registrar log: {e}")

    # Métodos para interagir com o banco de dados
    def inserir_dados(self, tabela, dados):
        self.banco_dados.inserir_dados(tabela, dados)

    def buscar_dados(self, tabela, colunas, condicao):
        return self.banco_dados.buscar_dados(tabela, colunas, condicao)

    def atualizar_dados(self, tabela, dados, condicao):
        self.banco_dados.atualizar_dados(tabela, dados, condicao)

    def deletar_dados(self, tabela, condicao):
        self.banco_dados.deletar_dados(tabela, condicao)
