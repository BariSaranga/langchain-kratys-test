# Kratys × LangChain validation deploy

Minimal LangChain agent used to validate that Kratys delivers on the three landing-page promises:

1. **"Talk to your infrastructure"** — Kratys's AI agent can read logs / status / findings for this deployed app
2. **"Deploy activity lands where you already review code"** — PR comments, commit status checks, GitHub Deployments tab
3. **"Ship secure code. Every time."** — 12-engine security scan runs on this deploy

## What this is

A FastAPI app that uses LangChain primitives (`PromptTemplate`, `RunnableLambda`) to build a chain. The chain returns canned responses (no LLM API key required for this validation pass).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | Health check (used by Kratys for auto-rollback) |
| POST | `/chat` | Chat with the agent. Body: `{"message": "..."}` |

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then hit `http://localhost:8000/chat` with a POST.

## Deploy via Kratys

1. Push this repo to GitHub
2. Open kratys.ai dashboard → `/new`
3. Connect GitHub → select this repo
4. Watch the deploy: provisioning → scan → build → live at `<slug>.kratys.ai`

Expected timing per Kratys's own claims: ~12 min first server (one-time), then <5 min per deploy.

## Notes for the validator

- The `/_debug/env` endpoint is **intentionally** insecure (echoes env vars). Kratys's static scanner should flag it. Used to validate the Fix-with-Kratys flow.
- `requirements.txt` has pinned versions to keep the security-scan dependency surface deterministic.
- Dockerfile is intentionally minimal — exercises Kratys's framework auto-detection.
