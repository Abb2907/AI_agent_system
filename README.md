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

## Component Breakdown

| Component | Role | Key Design |
|-----------|------|------------|
| **Planner** | Decides next action (use_tool or respond) | LLM-based; receives full context from prior steps; chain-aware |
| **Executor** | Runs the selected tool safely | Registry pattern; try-catch isolation; returns strings only |
| **Tool Registry** | Maps tool names → implementations | Abstract base class; plug-and-play new tools |
| **Agent Loop** | Orchestrates planner-executor iterations | Max 5 iterations; timed; caches results |
| **Cache** | LRU with TTL for repeated queries | SHA-256 keyed by query + recent history; 5-min expiry |
| **Metrics** | Tracks latency, tool usage, cache hits | Exposed via `/metrics` endpoint; percentile-based |
| **Auth** | JWT issuance and verification | Stateless; bcrypt hashing; rate-limited endpoints |
| **Database** | Persistent state for users/conversations | SQLAlchemy ORM; PostgreSQL primary, SQLite fallback |

---

## Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| **Planner-Executor over ReAct** | Cleaner separation of reasoning and action; easier to debug and test each in isolation | ReAct (single prompt loop) — less modular |
| **Keyword retrieval over vector DB** | Zero infrastructure dependency for demo; fast iteration; easy to swap later | FAISS/Chroma — requires embedding pipeline |
| **JWT over server sessions** | Stateless → horizontally scalable; no session store needed | Session cookies — simpler but stateful |
| **PostgreSQL over MongoDB** | ACID transactions for chat history; relational model fits user→conversation→message hierarchy | MongoDB — flexible schema but weaker consistency |
| **Groq over OpenAI** | 10x faster inference; free tier; compatible API surface | OpenAI — better models but slower/costlier |
| **LRU cache over Redis** | In-process = zero latency; sufficient for single-instance deployment | Redis — needed for multi-instance but adds infra |
| **AST calculator over `eval()`** | Prevents arbitrary code execution (security) | `eval()` — faster to implement but RCE risk |
| **Rate limiting per-IP** | Prevents abuse without requiring auth on public endpoints | Per-user limiting — requires auth, more complex |

---

## Design Trade-offs

| Trade-off | Current Choice | Impact |
|-----------|---------------|--------|
| **Context window (20 messages)** | Balance between relevance and token cost | More messages = better context but ~4x token cost |
| **Cache TTL (5 min)** | Prevents stale answers; short enough for dynamic data | Longer TTL = more hits but potentially outdated |
| **Max iterations (5)** | Prevents infinite loops; sufficient for 2-3 tool chains | Higher = handles more complex chains but risk of loops |
| **Temperature (0.2)** | Low for deterministic tool selection | Higher = more creative but less reliable planning |
| **Top-K retrieval (3 docs)** | Returns enough context without overwhelming LLM | Higher = better recall but adds noise + token cost |
| **History for cache key (last 5)** | Enough to differentiate context without over-specificity | Full history = fewer hits; no history = stale answers |

### Why These Values?

- **20-message context**: At ~100 tokens/message, this uses ~2K tokens — leaving 6K for tool results and generation. Cost-effective on free tier.
- **5-minute TTL**: Balances cache hit rate (~15-20% in typical usage) vs. freshness for web search results.
- **3 retrieval docs**: Empirically, 3 chunks provide sufficient grounding without exceeding context. Adding more shows diminishing returns in answer quality.

---

## Observability

The system exposes a `/metrics` endpoint with real-time operational data:

```json
GET /metrics

{
  "requests": {
    "total": 142,
    "errors": 3,
    "avg_latency_s": 2.41,
    "p50_s": 1.89,
    "p95_s": 4.12,
    "p99_s": 6.03
  },
  "cache": {
    "hits": 28,
    "misses": 114,
    "hit_rate_pct": 19.7
  },
  "tools": {
    "web_search": { "calls": 87, "success_rate_pct": 96.6, "avg_duration_s": 0.82 },
    "calculator": { "calls": 43, "success_rate_pct": 100.0, "avg_duration_s": 0.001 },
    "retriever":  { "calls": 52, "success_rate_pct": 100.0, "avg_duration_s": 0.003 }
  },
  "cache_detail": {
    "size": 34,
    "max_size": 128,
    "hits": 28,
    "misses": 114,
    "hit_rate_pct": 19.7
  }
}
```

### What's Tracked

- **Request latency** — End-to-end (P50, P95, P99) for SLA monitoring
- **Tool success rates** — Detects external API failures (Wikipedia down, etc.)
- **Cache performance** — Validates caching is reducing LLM calls

---

## Scaling Strategy

```
Current: Single-instance deployment (sufficient for <100 concurrent users)
```

### How this system would scale:

| Bottleneck | Solution | Effort |
|------------|----------|--------|
| **API throughput** | Horizontal scaling behind load balancer (stateless JWT = no session affinity needed) | Low |
| **Database** | Connection pooling (already via SQLAlchemy); read replicas for conversation history | Medium |
| **LLM rate limits** | Request queue with backpressure; multiple API keys; model fallback chain | Medium |
| **Cache invalidation** | Replace in-memory LRU with Redis for shared cache across instances | Low |
| **Document retrieval** | Migrate from keyword search to vector DB (FAISS → Pinecone for managed scaling) | Medium |
| **Background jobs** | Celery/RQ for document ingestion, embedding generation | Medium |

### Deployment Architecture at Scale

```
                    ┌─────────────┐
                    │  CDN/Nginx  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ FastAPI  │ │ FastAPI  │ │ FastAPI  │
        │ Instance │ │ Instance │ │ Instance │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             └──────┬──────┘─────────────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌─────────┐ ┌───────┐ ┌────────┐
    │PostgreSQL│ │ Redis │ │  Groq  │
    │ (Primary │ │(Cache)│ │  LLM   │
    │ +Replica)│ │       │ │  API   │
    └──────────┘ └───────┘ └────────┘
```

---

## License

MIT
