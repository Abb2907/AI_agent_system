# AI Agent Copilot

**A production-grade, multi-user AI agent system that reasons, selects tools, and executes multi-step tasks — not just another LLM wrapper.**

![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## The Problem

Most AI chatbots are stateless, single-turn, and can only generate text. They cannot:
- **Use tools** — no calculations, no data retrieval, no web search
- **Chain reasoning** — no multi-step problem solving
- **Remember context** — every conversation starts from scratch
- **Serve multiple users** — no isolation, no persistence

## The Solution

This project implements a **planner-executor agent architecture** where the AI decides *what to do*, *which tools to use*, and *in what order* — then executes the plan and synthesizes a grounded response.

```
User: "Find the population of France and calculate 10% of it"

  🧠 Thinking... → Decides to use web_search
  ⚡ web_search("population of France") → "67.75 million"
  🧠 Thinking... → Decides to use calculator
  ⚡ calculator("67750000 * 0.10") → "6775000.0"
  🧠 Thinking... → Has enough context, generating answer
  ✅ "The population of France is ~67.75M. 10% of that is 6,775,000."
```

Every step is logged, timed, and visible to the user in the reasoning panel.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS SPA)                  │
│              Auth UI  ·  Chat UI  ·  Reasoning Panel         │
└──────────────────────────┬───────────────────────────────────┘
                           │ REST API (JWT Auth)
┌──────────────────────────▼───────────────────────────────────┐
│                      FastAPI Backend                          │
│                                                               │
│  ┌─────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Auth   │  │  Rate Limit  │  │   CORS Middleware      │  │
│  │  (JWT)  │  │  (SlowAPI)   │  │                        │  │
│  └────┬────┘  └──────┬───────┘  └────────────────────────┘  │
│       │               │                                      │
│  ┌────▼───────────────▼──────────────────────────────────┐   │
│  │               API Routes                               │   │
│  │  /auth/signup  /auth/login  /query  /chat/*            │   │
│  └────────────────────────┬──────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼──────────────────────────────┐   │
│  │          Agent System (Planner → Executor Loop)        │   │
│  │                                                        │   │
│  │   Query → Plan → Execute → Plan → ... → Respond       │   │
│  │           (up to 5 iterations, with tool chaining)     │   │
│  └────────────┬───────────────────────────────────────────┘   │
│               │                                               │
│  ┌────────────▼──────────────────────────────────────────┐   │
│  │                  Tool Registry                         │   │
│  │  🧮 Calculator  │  📄 Retriever  │  🌐 Web Search    │   │
│  │  (AST-safe)     │  (Keyword)     │  (Wikipedia)       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL (+ SQLite fallback)             │   │
│  │   Users  ·  Conversations  ·  Messages  ·  Documents   │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Groq LLM   │
                    │ (Llama 3.3) │
                    └─────────────┘
```

### Agent Decision Flow

```
                    ┌──────────┐
                    │  Query   │
                    └────┬─────┘
                         ▼
                  ┌─────────────┐
                  │   Planner   │◄──── Context from
                  │  (LLM call) │      previous tools
                  └──────┬──────┘
                         │
                 ┌───────┴───────┐
                 ▼               ▼
           ┌──────────┐   ┌───────────┐
           │ use_tool  │   │  respond  │
           └─────┬────┘   └─────┬─────┘
                 ▼               ▼
           ┌──────────┐   ┌───────────┐
           │ Executor  │   │ Generate  │
           │ (run tool)│   │  Answer   │
           └─────┬────┘   └───────────┘
                 │
                 ▼
           Add result to
           context → loop
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Tool Chaining** | Agent chains multiple tools in sequence (Search → Calculate → Summarize) |
| **Reasoning Transparency** | Every decision, tool call, and timing is logged and visible in the UI |
| **Multi-User Isolation** | JWT auth with per-user conversations, messages, and history |
| **Persistent Memory** | Conversations survive across sessions in PostgreSQL |
| **Safe Execution** | Calculator uses AST parsing (no `eval`), tools are sandboxed |
| **Rate Limiting** | 20 req/min on queries, 10/min on login, 5/min on signup |
| **Production Patterns** | Structured logging, global error handling, env-based config |

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | **FastAPI** | Async-ready, auto-docs, dependency injection |
| Database | **PostgreSQL** + SQLAlchemy ORM | Production-grade persistence, SQLite fallback for dev |
| Auth | **JWT** (python-jose) + **bcrypt** | Stateless, scalable authentication |
| LLM | **Groq API** (Llama 3.3 70B) | Fast inference, free tier available |
| Search | **Wikipedia API** | Real-world knowledge, no API key needed |
| Rate Limiting | **SlowAPI** | Per-endpoint throttling |
| Deployment | **Docker** / **Render** | One-command deploy |

---

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL (or use SQLite for local dev — automatic fallback)

### 1. Clone & Setup

```bash
git clone https://github.com/<your-username>/ai-agent-system.git
cd ai-agent-system
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn openai python-dotenv httpx \
    sqlalchemy psycopg2-binary "python-jose[cryptography]" \
    "passlib[bcrypt]" slowapi alembic "pydantic[email]"
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
#   GROQ_API_KEY=<free key from https://console.groq.com>
#   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_agent_db
#   JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

### 4. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 — sign up, and start asking questions.

### Docker (Alternative)

```bash
docker build -t ai-agent .
docker run -p 8000:8000 --env-file .env ai-agent
```

---

## API Reference

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| `POST` | `/api/auth/signup` | — | 5/min | Create account |
| `POST` | `/api/auth/login` | — | 10/min | Get JWT token |
| `POST` | `/api/query` | Bearer | 20/min | Send query to agent |
| `GET` | `/api/chat/conversations` | Bearer | — | List conversations |
| `POST` | `/api/chat/conversations` | Bearer | — | Create conversation |
| `GET` | `/api/chat/conversations/:id` | Bearer | — | Get conversation + messages |
| `DELETE` | `/api/chat/conversations/:id` | Bearer | — | Delete conversation |
| `GET` | `/health` | — | — | Health check |

---

## Project Structure

```
ai-agent-system/
├── app/
│   ├── main.py                 # FastAPI app, middleware, lifespan
│   ├── agent/
│   │   ├── agent_loop.py       # Core agent loop with tool chaining
│   │   ├── planner.py          # LLM-based planning (decide next action)
│   │   └── executor.py         # Tool execution with error handling
│   ├── auth/
│   │   ├── auth.py             # JWT creation/verification, password hashing
│   │   └── dependencies.py     # FastAPI auth dependency injection
│   ├── db/
│   │   ├── database.py         # SQLAlchemy engine, session, init
│   │   └── models.py           # User, Conversation, Message, Document
│   ├── routes/
│   │   ├── auth.py             # Signup/Login endpoints
│   │   ├── chat.py             # Conversation CRUD
│   │   └── query.py            # Agent query endpoint
│   ├── services/
│   │   ├── llm.py              # Groq API client wrapper
│   │   └── prompt_builder.py   # Final answer prompt construction
│   └── tools/
│       ├── base_tool.py        # Abstract tool interface
│       ├── calculator.py       # Safe math (AST-based, no eval)
│       ├── retriever.py        # Document keyword search
│       └── web_search.py       # Wikipedia API integration
├── data/
│   └── documents.json          # Knowledge base documents
├── static/
│   └── index.html              # SPA frontend with reasoning panel
├── Dockerfile                  # Production container
├── render.yaml                 # Render.com deployment config
└── pyproject.toml              # Python project metadata
```

---

## What Makes This Different

This is **not** a tutorial chatbot that wraps an LLM API in a text box. This project demonstrates:

- **Agent architecture** — Planner-executor loop that reasons about *which tool to use and when*
- **Tool chaining** — Multi-step problem solving (retrieve data → calculate → summarize)
- **Reasoning transparency** — Every agent decision is timed, logged, and visible to the user
- **Production engineering** — JWT auth, rate limiting, structured logging, global error handling, SQL persistence
- **Security-conscious design** — AST-safe calculator (no `eval`), env-based secrets, bcrypt password hashing

> *"I built a multi-user AI agent system using a planner-executor architecture. It can decide when to use tools like retrieval or calculation, execute them, and generate grounded responses. The system includes persistent memory and is designed with scalable backend patterns."*

---

## License

MIT
