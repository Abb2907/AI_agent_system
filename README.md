# AI Agent System

An AI agent system that can reason, decide actions, use tools, and generate structured responses.

## Architecture

```
User Query → Planner → Tool Selection → Executor → LLM → Final Answer
```

### Components

- **Planner** – Decides whether to answer directly or use a tool
- **Executor** – Runs the selected tool and returns results
- **Agent Loop** – Orchestrates the reasoning flow (max 3 iterations)
- **Tools** – Calculator and Document Retriever
- **LLM Layer** – Generates planning decisions and final answers

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the server
uv run uvicorn app.main:app --reload
```

## API Usage

### Query Endpoint

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 25 * 18?"}'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Example Queries

| Query | Expected Behavior |
|-------|-------------------|
| "What is AI?" | Direct LLM response |
| "What is 25 * 18?" | Calculator tool → 450 |
| "What does the document say about revenue?" | Retriever tool → relevant chunks → LLM answer |

## Project Structure

```
ai-agent-system/
├── app/
│   ├── main.py              # FastAPI application
│   ├── agent/
│   │   ├── planner.py       # Decides action
│   │   ├── executor.py      # Runs tools
│   │   └── agent_loop.py    # Orchestration loop
│   ├── tools/
│   │   ├── base_tool.py     # Tool interface
│   │   ├── calculator.py    # Math evaluation
│   │   └── retriever.py     # Document retrieval
│   ├── services/
│   │   ├── llm.py           # OpenAI integration
│   │   └── prompt_builder.py
│   └── routes/
│       └── query.py         # API endpoints
├── data/
│   └── documents.json       # Sample documents
├── .env.example
├── pyproject.toml
└── README.md
```
