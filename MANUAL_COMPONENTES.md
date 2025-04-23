# Manual de Componentes do Bybit_Watcher

Este manual serve como referência central para todos os plugins, indicadores, monitoradores e gerenciadores do projeto Bybit_Watcher.

## Estrutura Geral
- **Plugin**: Componente modular, responsabilidade única, interface padronizada, autoidentificação e documentação.
- **Indicador**: Plugin especializado em cálculo/análise técnica (ex: RSI, ATR, médias móveis).
- **Monitorador**: Plugin focado em monitoramento de métricas externas (ex: funding, open interest, sentimento social, on-chain).
- **Gerenciador**: Orquestrador de plugins, controla ciclo de vida, execução e injeção de dependências.

---

## Plugins Principais

### sentinela
- **Responsabilidade**: Diagnóstico estratégico de sentimento de mercado, consolidando análise fundamental, técnica e monitoramento avançado.
- **Entradas**: Dados de mercado, indicadores, diagnósticos de monitoramento.
- **Saída**: Diagnóstico sintético, alertas, recomendações de risco, alavancagem e proteção.

### sinais_plugin
- **Responsabilidade**: Consolidação e emissão dos sinais finais de trading, integrando múltiplos timeframes e análises.
- **Entradas**: Diagnósticos de análise, sentinela e mercado.
- **Saída**: Sinal final (compra/venda/neutro) para execução.

---

## Indicadores (plugins/indicadores/)

### indicadores_tendencia
- **Responsabilidade**: Detecta tendência de mercado (ex: cruzamento de EMAs, ADX).

### indicadores_osciladores
- **Responsabilidade**: Cálculo de osciladores técnicos (ex: RSI, Estocástico).

### indicadores_volatilidade
- **Responsabilidade**: Mede volatilidade do mercado (ex: ATR, desvio padrão).

### indicadores_volume
- **Responsabilidade**: Analisa volume de negociação e padrões associados.

### outros_indicadores
- **Responsabilidade**: Indicadores técnicos diversos e complementares.

---

## Monitoradores (plugins/monitoramento/)

### funding_rate
- **Responsabilidade**: Monitora funding rate de derivativos, sinalizando risco de reversão ou squeeze.

### open_interest
- **Responsabilidade**: Monitora open interest, detectando movimentos de interesse e possíveis squeezes.

### orderbook
- **Responsabilidade**: Analisa clusters de ordens e liquidez no livro de ofertas.

### eventos_blockchain
- **Responsabilidade**: Sinaliza eventos críticos (halving, unlocks, vencimentos de opções, upgrades).

### onchain
- **Responsabilidade**: Monitora métricas on-chain (fluxo de stablecoins, movimentação de whales, NUPL, etc).

### monitor_ordens
- **Responsabilidade**: Monitoramento criterioso e prioritário de ordens/posições abertas.
- **Execução**: Só é ativado se `auto_trade` estiver `True` no config.
- **Frequência sugerida**: A cada 2 segundos para máxima segurança operacional.
- **Interface**: Método padronizado `diagnostico()` para integração com pipeline e gerenciadores.
- **Entradas**: Plugins de execução de ordens e conexão (injeção de dependências).
- **Saída**: Status, lista de ordens abertas e alertas institucionais (SL, TP, liquidação, etc).
- **Exemplo de integração**:
  ```python
  from plugins.monitoramento.monitor_ordens import MonitorOrdens
  monitor_ordens = MonitorOrdens(execucao_ordens=..., conexao=..., config=config)
  monitor_ordens.diagnostico()
  ```
- **Boas práticas**:
  - Rodar em thread/loop separado do ciclo macro.
  - Priorizar apenas pares com ordens abertas.
  - Garantir logs e tratamento criterioso de exceções.
  - Modular, seguro, testável e documentado.

### sentimento_social
- **Responsabilidade**: Analisa sentimento em redes sociais, buscas e notícias.

### correlatos
- **Responsabilidade**: Mede correlação do mercado cripto com ativos tradicionais (S&P500, DXY, ouro).

### anomalias
- **Responsabilidade**: Detecta outliers e anomalias em preço, volume e volatilidade.

### heatmap_liquidez
- **Responsabilidade**: Identifica zonas de liquidação e liquidez relevante no mercado.

### ml_preditor
- **Responsabilidade**: Previsão de movimentos de curto prazo via machine learning.

### custom_rules
- **Responsabilidade**: Permite definição de regras customizadas pelo usuário para alertas e diagnóstico.

---

## Gerenciadores (plugins/gerenciadores/)

### gerenciador_bot
- **Responsabilidade**: Orquestrador central do bot, controla ciclo principal, execução paralela e integração de todos os componentes.

### gerenciador_plugins
- **Responsabilidade**: Gerencia ciclo de vida, inicialização e execução dos plugins do sistema.

### gerenciador_banco
- **Responsabilidade**: Gerencia persistência, leitura e escrita no banco de dados.

### gerenciador_monitoramento
- **Responsabilidade**: Descobre, inicializa e executa todos os plugins de monitoramento, agregando diagnósticos avançados ao Sentinela.
- **Diferencial**: Possui sistema de auto plug-in, auto injeção e detecção de dependências.

#### Sistema de Auto Plug-in, Auto Injeção e Detecção de Dependências
- Descobre dinamicamente todos os plugins da pasta `monitoramento` (não requer registro manual).
- Consulta o método `dependencias()` de cada plugin para montar o grafo de dependências.
- Resolve e injeta dependências automaticamente, instanciando plugins na ordem correta.
- Detecta e loga ciclos de dependências, evitando loops e erros silenciosos.
- Loga todo o processo de descoberta, resolução e injeção, facilitando auditoria e debug.
- Se uma dependência não for encontrada, loga aviso e o plugin ainda pode ser carregado (com dependências faltantes).
- O fluxo é recursivo e robusto, pronto para expansão futura e fácil integração de novos plugins.

##### Fluxo resumido:
1. Descobre todas as classes de plugins de monitoramento.
2. Para cada plugin, consulta suas dependências via `dependencias()`.
3. Resolve e instancia recursivamente cada dependência, injetando via kwargs.
4. Detecta ciclos e loga qualquer problema de dependência.
5. Expõe os plugins prontos para uso pelo Sentinela e demais componentes.

##### Boas práticas:
- Cada plugin deve declarar corretamente suas dependências obrigatórias em `dependencias()`.
- Plugins devem ser modulares, responsabilidade única e documentados.
- O sistema é facilmente testável e auditável, promovendo segurança e clareza.

---

## Padrão Institucional de Auto Plug-in e Injeção

O sistema Bybit_Watcher agora adota um padrão global para todos os plugins e gerenciadores:
- **Auto plug-in**: Descoberta dinâmica de todos os plugins e gerenciadores via registro.
- **Auto injeção de dependências**: Resolução recursiva e criteriosa das dependências declaradas em cada componente.
- **Detecção de ciclos**: O sistema identifica e bloqueia ciclos de dependências, garantindo robustez.
- **Logs claros**: Todo o processo é logado para auditoria e debug.
- **Testabilidade**: O padrão facilita testes isolados e integração.

### Regras obrigatórias para Plugins e Gerenciadores
- `PLUGIN_NAME`: Obrigatório, único, descritivo.
- `dependencias()`: Deve retornar lista de nomes das dependências obrigatórias.
- `identificar_plugins()`: (Gerenciadores) Deve retornar o nome do gerenciador.
- Docstrings e comentários explicativos em todos os métodos e classes.
- Modularidade e responsabilidade única.

### Fluxo institucional
1. Descoberta dinâmica de classes via registro.
2. Montagem do grafo de dependências a partir de `dependencias()`.
3. Resolução recursiva das dependências, injetando instâncias já criadas.
4. Detecção e log de ciclos de dependências.
5. Instanciação e inicialização dos componentes na ordem correta.

### Exemplo de dependências cruzadas
- Um plugin de execução pode depender do plugin de banco e do plugin de sinais.
- O sistema garante que ambos estejam inicializados e injetados corretamente, sem risco de ciclo.

### Boas práticas adicionais
- Sempre documentar e atualizar o manual ao criar/alterar componentes.
- Usar logs para rastrear problemas de inicialização e dependências.
- Testar cenários de dependências ausentes ou ciclos propositalmente para garantir robustez.

---

## Boas Práticas
- Cada componente deve possuir docstring clara e completa.
- Responsabilidade única, modularidade e testabilidade são obrigatórios.
- Plugins e gerenciadores devem expor métodos de autoidentificação e dependências.
- Configurações sensíveis devem ser feitas via `.env` e `config.py`.

---

> **Este manual deve ser atualizado sempre que um novo componente for criado ou alterado!**
