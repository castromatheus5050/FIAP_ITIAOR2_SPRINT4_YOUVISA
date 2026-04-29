
# FIAP - Challenge YOUVISA (Sprint 4)


#[LINK DO VÍDEO](https://youtu.be/O5X9GYR8YKc) 

## Integrantes
- Bruno Castro - RM558359: https://www.linkedin.com/in/bruno-castro-dias/
- Hugo Mariano - RM560688: https://www.linkedin.com/in/hugomariano191628150/
- Matheus Castro - RM559293: https://www.linkedin.com/in/matheus-castro-63644b224/

Projeto de atendimento inteligente YOUVISA com backend Flask e interface React Native (Expo), focado em fluxo modular de agentes, interpretacao de perguntas e historico estruturado de interacoes.

## Estrutura do projeto

- `backend/`: API principal, orquestracao multiagente e persistencia SQLite.
- `frontend/`: interface do usuario para chat, consulta de processo e historico.
- `docs/`: documentacao da entrega e material complementar.
- `watson/`: artefatos de assistente (base inicial de intents/entities).

## Entrega Sprint 4 - O que foi implementado

- **Orquestracao multiagente** no backend, com agentes de:
  - governanca e protecao contra prompt injection;
  - interpretacao NLP (intent classification + entity extraction);
  - consulta de conhecimento/processo;
  - geracao de resposta controlada;
  - logging estruturado.
- **NLP aplicado** para identificar intencoes como status do processo, documentos, prazo, saudacao e despedida.
- **Extracao de entidades** com identificacao de `process_id` (ex.: `VISA-202401`) e tipo de documento citado.
- **Persistencia de interacoes** em SQLite (`backend/data/youvisa.db`) com sessao, pergunta, resposta, intent, entidades e timestamp.
- **API modular** com endpoints para chat, historico e consulta de processo.
- **Interface consolidada** com:
  - conversa com o chatbot;
  - painel de consulta rapida de processo;
  - exibicao de historico recente da sessao.

## Arquivos principais

- `backend/app.py`: API Flask com fluxo de agentes e governanca.
- `frontend/App.js`: UI de atendimento com chat + historico + status.
- `docs/sprint4-agentes-e-registro.md`: documento curto da Sprint 4.

## Fluxo funcional

1. Usuario envia pergunta no frontend.
2. Backend aplica filtro de governanca (escopo e injecao de prompt).
3. Agente NLP classifica intencao e extrai entidades.
4. Agente de conhecimento busca dados relevantes (ex.: status de processo).
5. Agente de resposta retorna texto controlado ao contexto YOUVISA.
6. Logger grava evento estruturado no banco.
7. Frontend atualiza chat e historico.

## Execucao local

### Backend

```bash
pip install -r backend/requirements.txt
python backend/app.py
```

### Frontend web (desktop)

```bash
cd frontend
npm install
npx expo install react-dom react-native-web
npm run web
```

## Variaveis de ambiente

Configurar em `backend/.env`:

```env
WATSON_API_KEY=...
WATSON_URL=...
WATSON_ASSISTANT_ID=...
WATSON_ENVIRONMENT_ID=...
WATSON_VERSION=2021-11-27
```

> O sistema funciona mesmo sem Watson configurado (fallback local controlado), mas usa Watson como apoio para perguntas nao cobertas pelos templates.

## Endpoints

- `GET /health`
- `POST /chat` -> `{ message, session_id?, user_id? }`
- `GET /history/<session_id>`
- `GET /process/<process_id>`
