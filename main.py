"""
Kratys validation test app — a minimal LangChain agent.

Purpose: validate that Kratys can deploy a LangChain-using Python app
end-to-end (provision → security scan → build → live URL). Returns canned
responses so no LLM API key is required for this pass.

The langchain imports here are real (not just dummy strings) so the
framework detector should identify this as a LangChain agent.
"""

import os
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

# Real langchain imports — proves framework-detection + dependency resolution
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

app = FastAPI(title="Kratys × LangChain validation", version="1.0.0")

# A canned-response "agent" built with langchain primitives so the detector
# sees the framework in use. Real LLM call would slot in via RunnableLambda
# in the same place; the structure is intentionally identical.
PROMPT = PromptTemplate.from_template("User asked: {question}")

CANNED_REPLIES = [
    "Hello from a Kratys-deployed LangChain agent.",
    "This agent is provisioned, scanned, and serving from a hardened DigitalOcean droplet.",
    "Twelve security engines reviewed me before I went live.",
    "I would normally call an LLM here, but this is a validation deploy.",
]


def _canned_response(prompt_text: str) -> str:
    # Deterministic pseudo-random selection based on prompt length so tests
    # can verify the agent is actually responsive without an LLM key.
    idx = len(prompt_text) % len(CANNED_REPLIES)
    return CANNED_REPLIES[idx]


chain = PROMPT | RunnableLambda(_canned_response)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    framework: str = "langchain"
    note: str = "deployed by kratys.ai"


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "live",
        "agent": "kratys-langchain-validation",
        "framework": "langchain",
        "endpoints": "GET / (health), POST /chat (agent), GET /health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    # Kratys uses this for health-check + auto-rollback
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    reply = chain.invoke({"question": req.message})
    return ChatResponse(reply=reply)


# Intentional minor security finding for Fix-with-Kratys validation:
# environment-variable echo without redaction. Static analyzer should flag.
@app.get("/_debug/env")
def _debug_env() -> dict[str, Optional[str]]:
    return {
        "FLAGGED_FOR_REMOVAL": os.environ.get("HOME"),
        "note": "kratys static-scan should flag this endpoint as data-exposure",
    }
