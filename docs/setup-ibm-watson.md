# Setup IBM Cloud + watsonx Assistant

## 1) Criar conta IBM Cloud
1. Acesse [IBM Cloud](https://cloud.ibm.com/registration).
2. Crie sua conta e confirme email.
3. Entre no console.

## 2) Criar recurso watsonx Assistant
1. No menu principal, clique em `Catalog`.
2. Pesquise por `watsonx Assistant` (ou `Watson Assistant`, conforme exibido no catalogo).
3. Selecione plano gratuito (Lite), quando disponivel.
4. Clique em `Create`.

## 3) Criar assistente
1. Abra o recurso criado.
2. Clique em `Launch`.
3. Crie um novo assistente.
4. Adicione uma `Action` ou `Dialog skill` (dependendo da interface exibida).
5. Use `watson/assistant-model-inicial.json` como base para cadastrar intents/entities/nodes manualmente.

## 4) Obter credenciais para backend Flask
No recurso watsonx Assistant, colete:
- `API Key`
- `URL`
- `Assistant ID`
- `Environment ID` (para PoC, prefira `draft environment id`)
- `Version` da API (pode usar `2021-11-27`)

Preencha em `backend/.env`:

```env
WATSON_API_KEY=...
WATSON_URL=...
WATSON_ASSISTANT_ID=...
WATSON_ENVIRONMENT_ID=...
WATSON_VERSION=2021-11-27
```

Opcional no payload do chat:
- `user_id` (se nao for enviado pelo frontend, o backend usa fallback para PoC).

## 5) Rodar backend Flask
No terminal:

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

API esperada em: `http://localhost:5000`

## 6) Rodar frontend React Native (Expo)
No terminal:

```bash
cd frontend
npm install
npm run start
```

No arquivo `frontend/App.js`, substitua:
- `API_BASE_URL = "http://SEU_IP_LOCAL:5000"`

Use o IP da sua maquina na rede local, por exemplo:
- `http://192.168.0.15:5000`

## 7) Checklist de validacao
- Backend responde `GET /health`.
- Frontend envia mensagem para `POST /chat`.
- Watson responde texto no app.
- Fluxo cobre: saudacao, agendamento, sintomas, horarios, emergencia, fallback.
- `backend/.env` carregado com todas as variaveis obrigatorias, incluindo `WATSON_ENVIRONMENT_ID`.
