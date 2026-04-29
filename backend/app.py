import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "youvisa.db"
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
CORS(app)


def _required_env(var_name: str) -> Optional[str]:
    value = os.getenv(var_name)
    return value.strip() if value else None


API_KEY = _required_env("WATSON_API_KEY")
SERVICE_URL = _required_env("WATSON_URL")
ASSISTANT_ID = _required_env("WATSON_ASSISTANT_ID")
ENVIRONMENT_ID = _required_env("WATSON_ENVIRONMENT_ID")
API_VERSION = _required_env("WATSON_VERSION") or "2021-11-27"


class GovernanceGuard:
    """Simple prompt injection and scope guard."""

    BLOCK_PATTERNS = [
        r"ignore .*?(previous|prior) instructions",
        r"reveal (your|the) (system|hidden) prompt",
        r"act as .* administrator",
        r"bypass .* policy",
        r"desconsidere .* instrucoes",
        r"mostre .* prompt",
        r"esque[çc]a .* regras",
    ]

    def validate(self, message: str) -> Optional[str]:
        if len(message) > 1000:
            return "Mensagem muito longa. Envie uma pergunta objetiva sobre vistos ou passaportes."

        lowered = message.lower()
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, lowered):
                return (
                    "Nao posso executar essa solicitacao. Posso ajudar com duvidas sobre "
                    "documentos, prazos e status do processo."
                )
        return None


class NLPInterpreterAgent:
    """Intent classification + entity extraction."""

    INTENT_PATTERNS = {
        "status_processo": [
            r"\bstatus\b",
            r"\bandamento\b",
            r"\bem que etapa\b",
            r"\bacompanhar\b",
        ],
        "documentos": [
            r"\bdocumento",
            r"\bdocumentacao\b",
            r"\brequisito",
            r"\bcomprovante",
        ],
        "prazo": [r"\bprazo\b", r"\bdemora\b", r"\btempo\b", r"\bquando\b"],
        "saudacao": [r"\bol[áa]\b", r"\boi\b", r"\bbom dia\b", r"\bboa tarde\b"],
        "despedida": [r"\bobrigad", r"\bvaleu\b", r"\btchau\b", r"\bencerrar\b"],
    }

    def classify_intent(self, message: str) -> str:
        lowered = message.lower()
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns):
                return intent
        return "desconhecida"

    def extract_entities(self, message: str) -> Dict[str, str]:
        entities: Dict[str, str] = {}
        process_match = re.search(
            r"\b(?:PRC|PROC|VISA)[-_]?\d{4,}\b", message.upper()
        )
        if process_match:
            entities["process_id"] = process_match.group(0).replace("_", "-")

        doc_match = re.search(
            r"\b(passaporte|rg|cpf|foto|comprovante de renda|reserva)\b",
            message.lower(),
        )
        if doc_match:
            entities["document_type"] = doc_match.group(0)
        return entities

    def run(self, message: str) -> Dict[str, Any]:
        return {
            "intent": self.classify_intent(message),
            "entities": self.extract_entities(message),
        }


class ProcessRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    entities_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS process_status (
                    process_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    visa_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

            existing = conn.execute(
                "SELECT COUNT(1) AS total FROM process_status"
            ).fetchone()
            if existing and existing["total"] == 0:
                now = datetime.now(timezone.utc).isoformat()
                conn.executemany(
                    """
                    INSERT INTO process_status (
                        process_id, applicant_name, visa_type, status, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "VISA-202401",
                            "Maria Souza",
                            "Turismo",
                            "Documentacao em analise",
                            now,
                        ),
                        (
                            "VISA-202402",
                            "Carlos Lima",
                            "Estudo",
                            "Entrevista agendada",
                            now,
                        ),
                    ],
                )

    def save_interaction(
        self,
        session_id: str,
        user_id: str,
        question: str,
        response: str,
        intent: str,
        entities_json: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO interaction_logs (
                    session_id, user_id, question, response, intent, entities_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_id, question, response, intent, entities_json, now),
            )

    def list_interactions(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, user_id, question, response, intent, entities_json, created_at
                FROM interaction_logs
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_process_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT process_id, applicant_name, visa_type, status, updated_at
                FROM process_status
                WHERE process_id = ?
                """,
                (process_id,),
            ).fetchone()
        return dict(row) if row else None


class KnowledgeAgent:
    def __init__(self, repository: ProcessRepository) -> None:
        self.repository = repository

    def run(self, intent: str, entities: Dict[str, str]) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        if intent == "status_processo":
            process_id = entities.get("process_id")
            if process_id:
                context["process"] = self.repository.get_process_status(process_id)
        return context


def _build_assistant_client() -> Optional[AssistantV2]:
    if not API_KEY or not SERVICE_URL or not ASSISTANT_ID or not ENVIRONMENT_ID:
        return None
    authenticator = IAMAuthenticator(API_KEY)
    assistant = AssistantV2(version=API_VERSION, authenticator=authenticator)
    assistant.set_service_url(SERVICE_URL)
    return assistant


class ResponseAgent:
    def __init__(self) -> None:
        self.assistant = _build_assistant_client()

    def _controlled_watson_fallback(self, message: str, session_id: str, user_id: str) -> str:
        if not self.assistant:
            return (
                "Nao encontrei essa informacao no fluxo atual. Pergunte sobre status do processo, "
                "documentos obrigatorios ou prazo medio."
            )
        try:
            watson_session = self.assistant.create_session(
                assistant_id=ASSISTANT_ID,
                environment_id=ENVIRONMENT_ID,
            ).get_result()
            scoped_message = (
                "Voce e o assistente YOUVISA. Responda apenas sobre solicitacao de visto e passaporte. "
                "Se a pergunta estiver fora de escopo, diga que nao pode responder.\n"
                f"Pergunta do usuario: {message}"
            )
            response = self.assistant.message(
                assistant_id=ASSISTANT_ID,
                environment_id=ENVIRONMENT_ID,
                session_id=watson_session["session_id"],
                input={"message_type": "text", "text": scoped_message},
                user_id=user_id,
            ).get_result()
            generic = response.get("output", {}).get("generic", [])
            texts = [
                item.get("text")
                for item in generic
                if item.get("response_type") == "text" and item.get("text")
            ]
            return texts[0] if texts else "Nao consegui gerar uma resposta no momento."
        except Exception:
            return (
                "Nao encontrei essa informacao no fluxo atual. Pergunte sobre status do processo, "
                "documentos obrigatorios ou prazo medio."
            )

    def run(
        self,
        message: str,
        intent: str,
        entities: Dict[str, str],
        context: Dict[str, Any],
        session_id: str,
        user_id: str,
    ) -> str:
        if intent == "saudacao":
            return (
                "Ola! Sou o assistente YOUVISA. Posso ajudar com status do processo, "
                "documentos necessarios e prazo medio."
            )
        if intent == "despedida":
            return "Perfeito. Se precisar, retome a conversa e sigo com seu atendimento."
        if intent == "documentos":
            return (
                "Para iniciar, normalmente pedimos passaporte valido, formulario preenchido, "
                "foto recente e comprovantes financeiros. Se quiser, detalho por tipo de visto."
            )
        if intent == "prazo":
            return (
                "O prazo varia por tipo de visto e consulado, mas em media fica entre 15 e 45 dias "
                "apos envio completo da documentacao."
            )
        if intent == "status_processo":
            process_id = entities.get("process_id")
            process = context.get("process")
            if not process_id:
                return "Informe o codigo do processo no formato VISA-202401 para consultar o andamento."
            if not process:
                return (
                    f"Nao localizei o processo {process_id}. Confira o codigo e tente novamente."
                )
            return (
                f"Processo {process['process_id']}: {process['status']}. "
                f"Solicitante: {process['applicant_name']}. "
                f"Tipo de visto: {process['visa_type']}."
            )
        return self._controlled_watson_fallback(message, session_id, user_id)


class LoggerAgent:
    def __init__(self, repository: ProcessRepository) -> None:
        self.repository = repository

    def run(
        self,
        session_id: str,
        user_id: str,
        question: str,
        response: str,
        intent: str,
        entities: Dict[str, str],
    ) -> None:
        self.repository.save_interaction(
            session_id=session_id,
            user_id=user_id,
            question=question,
            response=response,
            intent=intent,
            entities_json=json.dumps(entities, ensure_ascii=True),
        )


class MultiAgentOrchestrator:
    def __init__(self, repository: ProcessRepository) -> None:
        self.guard = GovernanceGuard()
        self.interpreter = NLPInterpreterAgent()
        self.knowledge = KnowledgeAgent(repository)
        self.responder = ResponseAgent()
        self.logger = LoggerAgent(repository)

    def run(self, message: str, session_id: str, user_id: str) -> Dict[str, Any]:
        blocked_reason = self.guard.validate(message)
        if blocked_reason:
            return {
                "session_id": session_id,
                "responses": [blocked_reason],
                "intent": "bloqueada_governanca",
                "entities": {},
            }

        nlp = self.interpreter.run(message)
        intent = nlp["intent"]
        entities = nlp["entities"]
        context = self.knowledge.run(intent, entities)
        answer = self.responder.run(message, intent, entities, context, session_id, user_id)

        self.logger.run(
            session_id=session_id,
            user_id=user_id,
            question=message,
            response=answer,
            intent=intent,
            entities=entities,
        )
        return {
            "session_id": session_id,
            "responses": [answer],
            "intent": intent,
            "entities": entities,
        }


repository = ProcessRepository(DB_PATH)
orchestrator = MultiAgentOrchestrator(repository)


@app.get("/health")
def health() -> tuple:
    return (
        jsonify(
            {
                "status": "ok",
                "watson_credentials_configured": bool(
                    API_KEY and SERVICE_URL and ASSISTANT_ID and ENVIRONMENT_ID
                ),
                "database": str(DB_PATH),
            }
        ),
        200,
    )


@app.get("/history/<session_id>")
def history(session_id: str) -> tuple:
    logs = repository.list_interactions(session_id=session_id)
    return jsonify({"session_id": session_id, "logs": logs}), 200


@app.get("/process/<process_id>")
def process_status(process_id: str) -> tuple:
    process = repository.get_process_status(process_id.upper())
    if not process:
        return jsonify({"error": "Processo nao encontrado."}), 404
    return jsonify(process), 200


@app.post("/chat")
def chat() -> tuple:
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    session_id = (payload.get("session_id") or "").strip() or str(uuid4())
    user_id = (payload.get("user_id") or "youvisa-user").strip()

    if not user_message:
        return jsonify({"error": "Field 'message' is required."}), 400

    try:
        result = orchestrator.run(user_message, session_id=session_id, user_id=user_id)
        return jsonify(result), 200
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
