# Sprint 4 - Orquestracao de Agentes Inteligentes no YOUVISA

## 1) Visao geral da arquitetura de orquestracao

Na Sprint 4, o projeto YOUVISA foi estruturado para operar em um fluxo de atendimento orientado por agentes, em vez de uma logica monolitica de "pergunta e resposta". Essa decisao atende ao requisito de organizacao multiagente e permite separar responsabilidades tecnicas (governanca, NLP, consulta de dados, geracao de resposta e auditoria).

A orquestracao principal ocorre no backend, pela classe `MultiAgentOrchestrator`, que coordena os agentes de forma sequencial e previsivel. O endpoint `POST /chat` recebe a mensagem do usuario, garante dados minimos de sessao e encaminha o processamento para esse orquestrador.

Em termos praticos, a aplicacao segue o ciclo:

1. Receber mensagem do usuario.
2. Validar seguranca e escopo da entrada.
3. Interpretar a intencao e extrair entidades.
4. Buscar contexto de negocio (quando necessario).
5. Gerar resposta controlada ao dominio YOUVISA.
6. Registrar a interacao para historico e rastreabilidade.

Esse desenho torna o atendimento mais robusto e facilita evolucao incremental: cada agente pode ser aprimorado sem reescrever o sistema inteiro.

## 2) Papel de cada agente no fluxo

### 2.1 GovernanceGuard (governanca e protecao)

O `GovernanceGuard` e o primeiro componente executado, funcionando como uma "barreira de entrada". Seu objetivo e evitar uso indevido do modelo e preservar o escopo de respostas do sistema.

Ele aplica regras como:

- bloqueio de padroes de prompt injection (ex.: pedidos para ignorar instrucoes);
- bloqueio de tentativas de acesso ao prompt interno;
- controle de tamanho de entrada (evitando textos excessivos).

Se a mensagem violar alguma regra, o fluxo nao segue para os demais agentes. O orquestrador retorna resposta de bloqueio com `intent = bloqueada_governanca`, garantindo comportamento seguro e padronizado.

### 2.2 NLPInterpreterAgent (compreensao da pergunta)

Quando a entrada passa na governanca, entra o `NLPInterpreterAgent`, responsavel por transformar texto livre em estrutura semantica.

Ele executa duas tarefas:

- **Classificacao de intencao**: identifica categorias como saudacao, prazo, documentos e status de processo.
- **Extracao de entidades**: localiza dados relevantes dentro da pergunta, principalmente `process_id` (ex.: `VISA-202401`) e termos de documentos.

O resultado desse agente e um objeto com `intent` e `entities`, que passa a orientar todo o restante do processamento.

### 2.3 KnowledgeAgent (contexto e dados de negocio)

O `KnowledgeAgent` faz a ponte entre NLP e dados persistidos. Ele consulta o repositorio quando a intencao demanda informacao factual, por exemplo:

- em `status_processo`, tenta localizar o processo solicitado no banco.

Esse componente reduz acoplamento: o agente de resposta nao precisa "saber consultar banco", apenas recebe contexto pronto.

### 2.4 ResponseAgent (resposta controlada)

O `ResponseAgent` construi a resposta final para o usuario. O comportamento e hibrido:

- para intencoes conhecidas (saudacao, prazo, documentos, status), responde por regras controladas;
- para intencoes desconhecidas, usa fallback controlado (com escopo YOUVISA), podendo consultar Watson quando configurado.

Assim, o sistema equilibra previsibilidade (respostas de negocio consistentes) com flexibilidade (fallback para perguntas menos estruturadas), mantendo principios de Prompt Engineering e delimitacao de escopo.

### 2.5 LoggerAgent (auditoria e historico)

Por fim, o `LoggerAgent` registra a interacao em log estruturado. O registro inclui dados suficientes para rastrear "o que foi perguntado", "como foi interpretado" e "o que foi respondido".

Esse mecanismo atende ao requisito de rastreabilidade e prepara a base para metricas futuras (intencoes mais frequentes, falhas de entendimento, tempo de atendimento, entre outros).

## 3) Sequencia de execucao no endpoint de chat

No endpoint `POST /chat`, o backend:

- recebe `message`, `session_id` (opcional) e `user_id` (opcional);
- gera um `session_id` quando necessario;
- valida obrigatoriedade da mensagem;
- chama `orchestrator.run(...)`.

No orquestrador, o caminho padrao e:

`GovernanceGuard -> NLPInterpreterAgent -> KnowledgeAgent -> ResponseAgent -> LoggerAgent`

Ao final, o backend retorna um payload estruturado para o frontend contendo:

- `session_id`;
- `responses` (lista de respostas);
- `intent`;
- `entities`.

Essa saida padronizada permite que a interface apresente nao so a resposta textual, mas tambem contexto da interpretacao (ex.: intencao detectada).

## 4) Registro estruturado das interacoes

As interacoes sao persistidas no SQLite (`backend/data/youvisa.db`), na tabela `interaction_logs`, com os campos:

- `session_id`
- `user_id`
- `question`
- `response`
- `intent`
- `entities_json`
- `created_at`

Beneficios diretos dessa modelagem:

- historico por sessao para acompanhamento do atendimento;
- rastreabilidade de decisoes do agente;
- insumo para analise de qualidade das respostas;
- base para governanca e auditoria de IA.

A aplicacao tambem expoe `GET /history/<session_id>`, permitindo recuperar o historico de forma simples para frontend e analise.

## 5) Como a orquestracao atende aos requisitos da Sprint 4

O desenho implementado cobre os itens centrais pedidos na atividade:

- **Fluxo multiagente estruturado**: agentes especializados com responsabilidades claras.
- **NLP aplicado**: classificacao de intencao e extracao de entidades.
- **Logs estruturados**: eventos de interacao persistidos com dados de sessao.
- **Arquitetura modular por servicos internos**: separacao em componentes com baixa dependencia.
- **Prompt Engineering e escopo controlado**: resposta orientada ao dominio YOUVISA.
- **Protecao contra prompt injection**: filtragem e bloqueio de padroes maliciosos.
- **Suporte a interface centrada no usuario**: frontend exibe resposta, historico e consulta de processo.

Em resumo, a orquestracao adotada transforma o chatbot em um fluxo de atendimento inteligente governavel, rastreavel e pronto para evolucoes futuras, mantendo alinhamento tecnico e funcional com os objetivos da Sprint 4.
