from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from memograph.graph import MemoGraphApp


load_dotenv()


DEFAULT_LOCAL_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}


def _normalize_origin(origin: str | None) -> str | None:
    if not origin:
        return None
    cleaned = origin.strip().rstrip("/")
    return cleaned or None


def _allowed_origins() -> list[str]:
    origins: set[str] = set(DEFAULT_LOCAL_ORIGINS)

    raw = os.getenv("CORS_ORIGINS", "")
    for origin in raw.split(","):
        normalized = _normalize_origin(origin)
        if normalized:
            origins.add(normalized)

    for env_name in ("FRONTEND_URL", "PUBLIC_FRONTEND_URL", "URL", "DEPLOY_PRIME_URL"):
        normalized = _normalize_origin(os.getenv(env_name))
        if normalized:
            origins.add(normalized)

    return sorted(origins)


@asynccontextmanager
async def lifespan(app: FastAPI):
    knowledge_dir = os.getenv("KNOWLEDGE_DIR", "knowledge")
    app.state.memo_app = MemoGraphApp(knowledge_dir=knowledge_dir)
    yield


app = FastAPI(
    title="MemoGraph API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    summary: str
    key_concepts: list[str]
    advanced_concepts: list[str]
    file_path: str
    content: str
    status: str
    related_topics: list[str]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, app_request: Request):
    try:
        memo_app: MemoGraphApp = app_request.app.state.memo_app
        result = await run_in_threadpool(memo_app.run, request.query)

        topic_file = Path(result["topic_file_path"])
        content = topic_file.read_text(encoding="utf-8") if topic_file.exists() else ""
        structured = result.get("structured_knowledge", {})

        return ChatResponse(
            answer=result["final_response"],
            summary=structured.get("summary", ""),
            key_concepts=structured.get("key_concepts", []),
            advanced_concepts=structured.get("advanced_concepts", []),
            file_path=result["topic_file_path"],
            content=content,
            status=result["file_status"],
            related_topics=result["related_topics"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
