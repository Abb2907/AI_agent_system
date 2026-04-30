# AI Copilot — Multi-User AI Agent System

A production-ready, multi-user AI agent system with persistent memory, JWT authentication, tool chaining, and a scalable backend architecture.

## What It Solves

Most AI chatbots are stateless, single-user toys. This system provides:
- **Multi-user isolation** — Each user has their own conversations, documents, and history
- **Persistent memory** — Conversations survive across sessions
- **Intelligent tool chaining** — Agent uses multiple tools in sequence (Search → Calculate → Summarize)
- **Production engineering** — Rate limiting, error handling, structured logging

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (SPA)                         │
│              Auth UI │ Chat UI │ Conversation History         │
└──────────────────────────┬───────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼───────────────────────────────────┐
│                     FastAPI Backend                           │
│  ┌─────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Auth   │  │  Rate Limit  │  │   CORS Middleware      │  │
│  │  (JWT)  │  │  (SlowAPI)   │  │                        │  │
│  └────┬────┘  └──────┬───────┘  └────────────────────────┘  │
│       │               │                                      │
│  ┌────▼───────────────▼──────────────────────────────────┐   │
│  │              API Routes                                │   │
│  │   /auth/signup  /auth/login  /query  /chat/*          │   │
│  └────────────────────────┬──────────────────────────────┘   │
│                           │                                   │
│  ┌────────────────────────▼──────────────────────────────┐   │
│  │              Agent System (Planner-Executor)           │   │
│  │                                                        │   │
│  │   Query → Plan → Execute Tool → Plan → ... → Respond  │   │
│  │                    (Tool Chaining)                      │   │
│  └────────────┬───────────────────────────────────────────┘   │
│               │                                               │
│  ┌────────────▼───────────────────────────────────────────┐   │
│  │                Available Tools                          │   │
│  │   Calculator  │  Retriever  │  Web Search              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL Database                         │   │
│  │   Users │ Conversations │ Messages │ Documents          │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Groq LLM   │
                    │  (Llama 3)  │
                    └─────────────┘
```

## Agent Loop — Tool Chaining

```
User Query: "Find the population of France and calculate 10% of it"

Iteration 1: Plan → use_tool("web_search", "population of France")
             Execute → "67.75 million"

Iteration 2: Plan → use_tool("calculator", "67750000 * 0.10")
             Execute → "6775000.0"

Iteration 3: Plan → respond
             Generate final answer with all context
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JS SPA |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt |
| LLM | Groq API (Llama 3.3 70B) |
| Rate Limiting | SlowAPI |
| Deployment | Docker / Render |

## Setup Instructions

### Prerequisites
- Python 3.12+
- PostgreSQL running locally (or Docker)

### 1. Clone & Virtual Environment

```bash
git clone <repo-url>
cd ai-agent-system
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn openai python-dotenv httpx \
    sqlalchemy psycopg2-binary "python-jose[cryptography]" \
    "passlib[bcrypt]" slowapi alembic "pydantic[email]"
```

### 3. Set Up PostgreSQL

```bash
# Option A: Local PostgreSQL
createdb ai_agent_db

# Option B: Docker
docker run -d --name ai-agent-db \
    -e POSTGRES_DB=ai_agent_db \
    -e POSTGRES_PASSWORD=postgres \
    -p 5432:5432 postgres:16
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
#   GROQ_API_KEY=your-key (free at https://console.groq.com)
#   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_agent_db
#   JWT_SECRET_KEY=your-strong-random-secret
```

### 5. Run the Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup` | No | Create account |
| POST | `/api/auth/login` | No | Get JWT token |
| POST | `/api/query` | Yes | Send query to agent |
| GET | `/api/chat/conversations` | Yes | List conversations |
| POST | `/api/chat/conversations` | Yes | Create conversation |
| GET | `/api/chat/conversations/:id` | Yes | Get conversation + messages |
| DELETE | `/api/chat/conversations/:id` | Yes | Delete conversation |
| GET | `/health` | No | Health check |

## Design Decisions

1. **Planner-Executor Architecture** — Separates reasoning from action, allowing the agent to chain tools dynamically
2. **JWT over sessions** — Stateless auth scales horizontally; no server-side session storage needed
3. **PostgreSQL** — ACID compliance for chat history; supports concurrent multi-user access
4. **Rate limiting per IP** — Prevents API abuse; 20 requests/minute on the query endpoint
5. **Conversation context window** — Last 20 messages loaded for context, balancing relevance vs. token cost

## Project Structure

```
ai-agent-system/
├── app/
│   ├── main.py              # FastAPI app with lifespan, middleware
│   ├── auth/
│   │   ├── auth.py          # JWT creation/verification, password hashing
│   │   └── dependencies.py  # FastAPI auth dependency injection
│   ├── db/
│   │   ├── database.py      # SQLAlchemy engine, session factory
│   │   └── models.py        # User, Conversation, Message, Document
│   ├── agent/
│   │   ├── agent_loop.py    # Main agent loop with tool chaining
│   │   ├── planner.py       # LLM-based planning with chain awareness
│   │   └── executor.py      # Tool execution with error handling
│   ├── routes/
│   │   ├── auth.py          # Signup/Login endpoints
│   │   ├── chat.py          # Conversation CRUD
│   │   └── query.py         # Agent query endpoint (rate limited)
│   ├── services/
│   │   ├── llm.py           # Groq LLM client
│   │   └── prompt_builder.py
│   └── tools/
│       ├── base_tool.py     # Abstract tool interface
│       ├── calculator.py
│       ├── retriever.py
│       └── web_search.py
├── static/
│   └── index.html           # SPA with auth + chat UI
├── data/
│   └── documents.json       # RAG document store
├── Dockerfile
├── .env.example
└── pyproject.toml
```

## Docker Deployment

```bash
docker build -t ai-copilot .
docker run -p 8000:8000 --env-file .env ai-copilot
```

Or use the included `render.yaml` for one-click Render deployment.

## License

MIT
