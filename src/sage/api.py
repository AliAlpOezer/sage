"""HTTP wrapper exposing the RAG query loop to the Atlas (Next.js) UI.

    uv run uvicorn sage.api:app --port 8000

The Python pipeline stays the backend of record; TypeScript survives only in
the UI layer, which calls POST /ask and renders the answer + sources.
"""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sage.service import EmptyIndex
from sage.service import answer as run_answer

app = FastAPI(title="Sage RAG")

# The Next.js dev server calls this from the browser during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    k: int | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/ask")
def ask(req: AskRequest) -> dict:
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")
    try:
        result = run_answer(req.question, req.k)
    except EmptyIndex as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"answer": result.answer, "sources": [asdict(s) for s in result.sources]}
