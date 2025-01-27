# Bot de Trading para Criptomoedas

<img src="assets/bybit_watcher_logo.png" alt="Logo do Bot" width="200">

Este bot de trading foi desenvolvido para operar no mercado de futuros de criptomoedas da Bybit, com foco em gerar sinais de compra e venda de forma autônoma, criteriosa, segura e eficiente.

O bot utiliza uma arquitetura de plugins para facilitar a implementação e a manutenção das estratégias de trading.

**Funcionalidades:**

- Coleta de dados de mercado da Bybit, usando a biblioteca CCXT.
- Armazenamento dos dados em um banco de dados PostgreSQL.
- Análise de candles para identificar padrões e classificá-los.
- Cálculo de indicadores técnicos, como médias móveis, RSI, MACD, etc.
- Geração de sinais de compra e venda com base na análise de candles e indicadores técnicos.
- Cálculo da alavancagem ideal para cada operação, com base na volatilidade do mercado.
- Exibição dos sinais de trading no console.
- (Em desenvolvimento) Integração com a API Gemini do Google para complementar a análise do mercado.
- (Futuro) Execução automática de ordens na Bybit.
- (Futuro) Gerenciamento de risco, com stop-loss e take-profit.

**Plugins:**

- `analise_candles.py`: Analisa os candles e gera sinais de trading.
- `armazenamento.py`: Armazena os dados das velas no banco de dados.
- `banco_dados.py`: Gerencia o banco de dados PostgreSQL.
- `calculo_alavancagem.py`: Calcula a alavancagem ideal para as operações.
- `conexao.py`: Estabelece e gerencia a conexão com a Bybit.
- `execucao_ordens.py`: Exibe os sinais de trading.
- `indicadores/`:
  - `indicadores_tendencia.py`: Calcula indicadores de tendência e gera sinais de trading.
  - `indicadores_osciladores.py`: Calcula indicadores osciladores e gera sinais de trading.
  - `indicadores_volatilidade.py`: Calcula indicadores de volatilidade e gera sinais de trading.
- `outros_indicadores.py`: Calcula outros indicadores e gera sinais de trading.
- `analise_mercado.py`: (Em desenvolvimento) Analisa o mercado usando diferentes fontes de dados.

**Regras de Ouro:**

1. **Autônomo:** O bot deve operar de forma independente, sem intervenção humana.
2. **Criterioso:** O bot deve ser rigoroso na análise dos dados e na tomada de decisões.
3. **Seguro:** O bot deve priorizar a segurança do capital.
4. **Certeiro:** O bot deve buscar a maior precisão possível na geração de sinais.
5. **Eficiente:** O bot deve ser eficiente no uso de recursos computacionais.
6. **Clareza:** O código do bot deve ser claro, conciso e bem organizado.
7. **Modular:** O código deve ser dividido em módulos independentes e reutilizáveis.
8. **Composto por plugins:** O bot deve usar uma arquitetura de plugins para facilitar a adição de novas funcionalidades.
9. **Testável:** Cada módulo e função deve ser testável de forma independente.
10. **Documentado:** O código deve ser documentado com clareza, usando docstrings e comentários.
11. **Dinamismo:** O bot deve se adaptar às condições do mercado, ajustando as estratégias e parâmetros de acordo com a volatilidade, o volume e outros fatores relevantes.

**Como executar o bot:**

1. Clone o repositório do GitHub.
2. Crie um ambiente virtual e instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente no arquivo `.env`.
4. Execute o script `main.py`: `python main.py`

**Observações:**

- O bot ainda está em desenvolvimento e precisa de mais testes e refinamento.
- As estratégias de trading implementadas no bot não garantem lucros e podem resultar em perdas financeiras.
- Use o bot com cuidado e por sua conta e risco.
