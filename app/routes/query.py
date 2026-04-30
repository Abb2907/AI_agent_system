from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.agent_loop import run_agent
from app.tools.calculator import CalculatorTool
from app.tools.retriever import RetrieverTool
from app.tools.web_search import WebSearchTool

router = APIRouter()

# Register available tools
TOOLS = [CalculatorTool(), RetrieverTool(), WebSearchTool()]


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    steps: list[dict]


@router.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    """Accept a user query and run it through the agent system."""
    result = run_agent(query=request.query, tools=TOOLS)
    return QueryResponse(answer=result["answer"], steps=result["steps"])
