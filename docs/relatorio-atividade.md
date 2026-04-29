# Relatorio da Atividade - Assistente Conversacional com NLP

## 1. Objetivo

Este projeto apresenta uma prova de conceito (PoC) de assistente conversacional para atendimento inicial no contexto de saude, utilizando backend em Python com Flask, integracao com watsonx Assistant (IBM), e interface de interacao com o usuario em React Native (Expo).

O foco da implementacao foi garantir um fluxo direto e funcional, conforme solicitado, sem aprofundamento em tratamento de edge-cases complexos.

## 2. Arquitetura da Solucao

A solucao foi organizada em tres blocos principais:

- **Frontend (React Native / Expo):** interface de chat para envio e recebimento de mensagens.
- **Backend (Flask):** camada intermediaria para comunicacao entre frontend e watsonx Assistant.
- **Assistente Conversacional (watsonx Assistant):** motor NLP responsavel por identificar intencoes e gerar respostas.

Fluxo tecnico de comunicacao:

1. O usuario envia uma mensagem pela interface.
2. O frontend faz requisicao HTTP `POST /chat` para o backend.
3. O backend cria ou reutiliza uma sessao (`session_id`) no watsonx Assistant.
4. O backend encaminha a mensagem para a API do assistente.
5. O watsonx retorna a resposta com base no fluxo conversacional configurado.
6. O backend devolve a resposta ao frontend.
7. O frontend exibe a resposta ao usuario no chat.

## 3. Modelagem Conversacional

Foi definido um modelo inicial de conversa com intents, entities e fluxo de dialogo, armazenado em `watson/assistant-model-inicial.json`, para cadastro no ambiente IBM.

### 3.1 Intents principais

- `#saudacao`
- `#despedida`
- `#agendar_consulta`
- `#dvida_sintoma`
- `#horario_atendimento`
- `#emergencia`
- `#fallback`

### 3.2 Entities principais

- `@sintoma`: febre, tosse, dor de cabeca, dor no peito, falta de ar.
- `@periodo`: manha, tarde, noite.

### 3.3 Fluxo implementado

O fluxo contempla:

- atendimento inicial com saudacao;
- suporte a agendamento de consulta;
- orientacao inicial para sintomas;
- informacao de horarios de atendimento;
- orientacao prioritaria para emergencia;
- tratamento de excecao com fallback para mensagens nao reconhecidas.

## 4. Implementacao do Backend

O backend foi implementado em Flask e exposto com dois endpoints:

- `GET /health`: verifica status da API e configuracao basica.
- `POST /chat`: recebe mensagem do usuario, gerencia sessao e retorna respostas do assistente.

Foram utilizadas as bibliotecas:

- `flask`
- `flask-cors`
- `python-dotenv`
- `ibm-watson`

Variaveis de ambiente necessarias:

- `WATSON_API_KEY`
- `WATSON_URL`
- `WATSON_ASSISTANT_ID`
- `WATSON_ENVIRONMENT_ID` (na PoC, utilizado `draft environment id`)
- `WATSON_VERSION`

## 5. Interface com o Usuario

A interface foi desenvolvida em React Native (Expo), com um layout simples de chat:

- campo de texto para entrada de mensagens;
- botao de envio;
- exibicao de mensagens do usuario e do assistente em bolhas.

Para testes em desktop, foi utilizado o modo web do Expo, com `API_BASE_URL` configurada para `http://localhost:5000`.

## 6. Validacao da PoC

A validacao foi conduzida com abordagem direta, priorizando funcionamento basico:

- verificacao de subida do backend;
- teste de conectividade frontend-backend;
- teste de resposta do assistente para mensagens de saudacao e intencoes centrais.

Durante a integracao, foram ajustados dois pontos tecnicos relevantes:

1. obrigatoriedade de `environment_id` na chamada da API do Watson;
2. obrigatoriedade de `user_id` em requisicoes de mensagem, com fallback no backend para a PoC.

Com esses ajustes, o fluxo principal passou a operar de forma estavel para o escopo da atividade.

## 7. Conclusao

O projeto atingiu o objetivo proposto para a atividade: implementacao de um assistente conversacional com NLP, integrado a backend Python e interface de interacao com usuario, dentro de um cenario de atendimento inicial em saude.

A solucao esta estruturada para evolucao futura, permitindo extensao de intents, refinamento de entidades, melhoria do fluxo conversacional e expansao de validacoes em etapas posteriores.

