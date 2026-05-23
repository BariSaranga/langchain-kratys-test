"""
Kratys validation test app — a minimal LangChain agent backed by OpenAI.

Purpose: validate that Kratys can deploy a LangChain-using Python app
end-to-end (provision → security scan → build → live URL → real LLM call).

Requires OPENAI_API_KEY to be injected by Kratys at deploy time. If not
set, /chat returns a clear 503 explaining the missing config — better
than a 500 stacktrace for the validation-table walkthrough.
"""

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


app = FastAPI(title="Kratys × LangChain validation", version="2.0.0")


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a witty AI assistant deployed by Kratys.ai. Keep replies "
            "under 200 characters. Mention you're running on a hardened "
            "droplet only if the user asks about your infrastructure.",
        ),
        ("user", "{question}"),
    ]
)


def _build_chain():
    """Lazy-build chain so the import doesn't crash on missing key."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    llm = ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=0.7,
        timeout=20,
    )
    return PROMPT | llm | StrOutputParser()


CHAIN = _build_chain()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    framework: str = "langchain"
    model: str = ""
    note: str = "deployed by kratys.ai"


@app.get("/")
def root() -> dict[str, object]:
    return {
        "status": "live",
        "agent": "kratys-langchain-validation",
        "framework": "langchain",
        "llm_configured": CHAIN is not None,
        "endpoints": "GET / (health), POST /chat (agent), GET /health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if CHAIN is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY not set. Add it via the Kratys project "
                "environment-variables UI and redeploy."
            ),
        )
    try:
        reply = CHAIN.invoke({"question": req.message})
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream LLM call failed: {type(e).__name__}: {e}",
        )
    return ChatResponse(
        reply=reply.strip(),
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    )


# Intentional minor security finding for Fix-with-Kratys validation:
# environment-variable echo without redaction. Static analyzer should flag.
@app.get("/_debug/env")
def _debug_env() -> dict[str, Optional[str]]:
    return {
        "FLAGGED_FOR_REMOVAL": os.environ.get("HOME"),
        "note": "kratys static-scan should flag this endpoint as data-exposure",
    }
