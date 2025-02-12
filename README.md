<img src="assets/bybit_watcher_logo.png" alt="Logo do Bot" width="200">

## Bybit_Watcher

**Descrição do projeto:**

O Bybit_Watcher é um bot de trading automatizado para a plataforma Bybit, projetado para monitorar o mercado, analisar dados e gerar sinais de trading. O bot é construído com foco em modularidade, segurança e extensibilidade, permitindo que traders e desenvolvedores personalizem e expandam suas funcionalidades.

**Funcionalidades principais:**

- Monitoramento de mercado em tempo real
- Análise de candlesticks
- Cálculo de médias móveis
- Identificação de padrões de price action
- Cálculo de alavancagem e risco
- Geração de sinais de trading
- Execução de ordens (em desenvolvimento)
- Armazenamento de dados em banco de dados
- Logging detalhado das atividades do bot

**Público-alvo:**

- Traders que desejam automatizar suas estratégias de trading na Bybit
- Desenvolvedores que desejam criar e integrar seus próprios plugins e indicadores

**Instalação e Configuração:**

**Dependências:**

- Python 3.7 ou superior
- Bibliotecas Python:
  - bybit
  - TA-Lib
  - mplfinance
  - python-dotenv
  - outras bibliotecas listadas no arquivo requirements.txt

**Como instalar:**

1. Clone o repositório: `git clone https://github.com/MarcusAbenAthar/Bybit_Watcher.git`
2. Crie um ambiente virtual: `python -m venv.venv`
3. Ative o ambiente virtual:
   - Linux/macOS: `source.venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. Instale as dependências: `pip install -r requirements.txt`

**Configurações:**

1. Crie um arquivo `.env` na raiz do projeto.
2. Adicione as seguintes variáveis de ambiente ao arquivo `.env`:
   - `BYBIT_API_KEY`: Sua chave de API da Bybit
   - `BYBIT_API_SECRET`: Seu segredo de API da Bybit
   - `DB_USER`: Usuário do banco de dados
   - `DB_PASSWORD`: Senha do banco de dados
   - `DB_NAME`: Nome do banco de dados
   - Outras configurações relevantes para o bot

**Uso:**

**Como executar:**

1. Ative o ambiente virtual (se ainda não estiver ativo).
2. Execute o arquivo `main.py`: `python main.py`

**Comandos e opções:**

- O bot atualmente não oferece comandos ou opções adicionais.
- Em desenvolvimento: modos de operação como backtesting e live trading.

**Exemplos de uso:**

- **Monitorar o mercado e gerar sinais:** Execute o bot com as configurações padrão para monitorar o mercado e gerar sinais de trading.
- **Desenvolver novos plugins:** Crie um novo arquivo Python no diretório `plugins` e implemente a classe do plugin herdando da classe base `Plugin`.

**Plugins:**

**Descrição dos plugins:**

- **`conexao.py`:** Gerencia a conexão com a API da Bybit.
- **`banco_dados.py`:** Realiza operações de banco de dados.
- **`calculo_alavancagem.py`:** Calcula a alavancagem ideal para cada operação.
- **`calculo_risco.py`:** Calcula o risco de cada operação.
- **`analise_candles.py`:** Analisa os candlesticks para identificar padrões e tendências.
- **`medias_moveis.py`:** Calcula e analisa médias móveis.
- **`price_action.py`:** Analisa o movimento dos preços para identificar suportes, resistências e padrões.
- **`validador_dados.py`:** Valida os dados recebidos da API e de outras fontes.
- **`sinais_plugin.py`:** Gera sinais de compra e venda.
- **`gerenciador_banco.py`:** Gerencia as operações do banco de dados.
- **`gerenciador_bot.py`:** Gerencia o funcionamento do bot.
- **`gerenciador_plugins.py`:** Gerencia os plugins do bot.

**Como criar novos plugins:**

1. Crie um novo arquivo Python no diretório `plugins`.
2. Implemente a classe do plugin herdando da classe base `Plugin`.
3. Registre o plugin no `gerenciador_plugins.py`.

**Contribuição:**

**Como contribuir:**

- Sinta-se à vontade para enviar pull requests com correções de bugs, melhorias de código e novos plugins.
- Relate bugs e sugestões de melhorias na seção de Issues do repositório.

**Código de conduta:**

- Seja respeitoso e colaborativo com os outros contribuidores.
- Siga as boas práticas de desenvolvimento de software.

**Outras informações relevantes:**

**Licença:**

- MIT License

**Agradecimentos:**

- Agradeço à comunidade de desenvolvedores de código aberto por fornecer ferramentas e recursos valiosos.

**Observações:**

- Este README.md foi gerado com base nas informações fornecidas até o momento.
- É importante revisar e atualizar este arquivo com mais detalhes e informações relevantes sobre o projeto.
