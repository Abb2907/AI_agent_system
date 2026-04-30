import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.agent.agent_loop import run_agent
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Conversation, Message, User
from app.tools.calculator import CalculatorTool
from app.tools.retriever import RetrieverTool
from app.tools.web_search import WebSearchTool

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Register available tools
TOOLS = [CalculatorTool(), RetrieverTool(), WebSearchTool()]


class QueryRequest(BaseModel):
    query: str
    conversation_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    steps: list[dict]
    conversation_id: str


@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/minute")
def handle_query(
    request: Request,
    body: QueryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a user query, run through the agent, and persist the conversation."""
    # Get or create conversation
    if body.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == body.conversation_id,
                Conversation.user_id == user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation with query as title
        title = body.query[:100] if len(body.query) > 100 else body.query
        conversation = Conversation(user_id=user.id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Build conversation history for context
    previous_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .limit(20)  # Last 20 messages for context window
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in previous_messages]

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.query,
    )
    db.add(user_msg)

    # Run agent with conversation history
    result = run_agent(query=body.query, tools=TOOLS, history=history)

    # Save assistant response
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        tool_steps=json.dumps(result["steps"]),
    )
    db.add(assistant_msg)
    db.commit()

    return QueryResponse(
        answer=result["answer"],
        steps=result["steps"],
        conversation_id=str(conversation.id),
    )

