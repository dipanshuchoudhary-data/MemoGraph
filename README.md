<h1 align="center">🧠 MemoGraph</h1>

<p align="center">
  <b>Build a living Markdown knowledge base with an agentic workflow.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/LangGraph-Agentic%20Workflow-8A2BE2?style=for-the-badge" alt="LangGraph" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vite-Frontend-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
</p>

---

## ✨ What is MemoGraph?

**MemoGraph is not a chatbot.**  
It is a knowledge-building system that:

- takes your query,
- researches and summarizes it,
- writes/updates topic Markdown files,
- links related topics,
- and improves the knowledge base over time.

Think of it as a **personal knowledge graph in Markdown form**.

---

## 🧩 How it works

```text
Start → Research → Summarize → Write → Link → End
```

| Agent | Responsibility |
|---|---|
| `Master Agent` | Orchestrates the workflow via LangGraph `StateGraph` |
| `Research Agent` | Produces raw research notes from your query |
| `Summarizer Agent` | Converts notes into structured knowledge |
| `Writer Agent` | Creates/updates topic file without blind overwrite |
| `Linking Agent` | Connects related topics and updates links bidirectionally |

### Shared state (high level)

`user_query`, `topic_name`, `raw_research`, `structured_knowledge`, `topic_file_path`, `related_topics`, `final_response`

---

## 📁 Project structure

```text
MemoGraph/
├─ memograph/          # Core workflow, state, models, markdown logic
├─ knowledge/          # Generated/updated topic markdown files
├─ frontend/           # React + Vite UI
├─ server.py           # FastAPI backend
└─ README.md
```

---

## ⚙️ Setup

1. Use **Python 3.12+**.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Add environment variables in a `.env` file at repo root:

```env
OPENAI_API_KEY=
OPENAI_MODEL=openai/gpt-4.1-mini
OPENAI_BASE_URL=https://openrouter.ai/api/v1
KNOWLEDGE_DIR=knowledge
```

> If `OPENAI_API_KEY` is missing, MemoGraph falls back to a deterministic local model so the workflow still runs.

---

## 🚀 Run from CLI

```bash
python -m memograph.cli "Graph neural networks for recommendation systems"
```

Show the updated markdown after execution:

```bash
python -m memograph.cli "Graph neural networks for recommendation systems" --show-markdown
```

---

## 🌐 Run API backend

Start backend:

```bash
python server.py
```

Available endpoints:

- `GET /health`
- `POST /chat`

Example request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Graph neural networks for recommendation systems"}'
```

---

## Run frontend + backend

In terminal 1:

```bash
python server.py
```

In terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Then open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`

---

## 🔁 Progressive learning example

Run a topic twice with increasing depth:

```bash
python -m memograph.cli "Graph neural networks for recommendation systems"
python -m memograph.cli "Advanced graph neural networks for recommendation systems in production"
