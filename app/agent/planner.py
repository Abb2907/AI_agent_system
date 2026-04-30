import json
import logging
import re

from app.services.llm import call_llm
from app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a planning module for an AI agent. Given the user's query and available tools, decide the best action.

Available tools:
{tools_description}

Respond ONLY with valid JSON in this exact format:
- If a tool is needed: {{"action": "use_tool", "tool_name": "<name>", "parameters": "<input for the tool>"}}
- If you can answer directly: {{"action": "respond"}}

Rules:
- Use "calculator" for any math/arithmetic expressions.
- Use "retriever" for questions about documents, files, or stored knowledge.
- Use "web_search" for questions about real-world facts, people, places, current events, or topics not covered by local documents.
- Use "respond" when you already have enough information from previous tool results to answer the query.
- You can chain multiple tools: retrieve data first, then calculate, then respond.
- If previous tool results already provide enough information, use "respond".
- Do NOT include any explanation, only the JSON object.
{tools_used_note}"""


def plan(query: str, tools: list[BaseTool], context: str = "", tools_used: list[str] | None = None) -> dict:
    """Decide whether to use a tool or respond directly.

    Args:
        query: The user's question
        tools: Available tools
        context: Context from previous steps
        tools_used: List of tools already used in this chain

    Returns a dict with keys:
        action: "use_tool" or "respond"
        tool_name: (optional) name of the tool to use
        parameters: (optional) input string for the tool
    """
    tools_desc = "\n".join(f"- {t.name}: {t.description}" for t in tools)

    tools_used_note = ""
    if tools_used:
        tools_used_note = f"\nTools already used in this chain: {', '.join(tools_used)}. Only use another tool if more information is needed."

    system_prompt = PLANNER_SYSTEM_PROMPT.format(
        tools_description=tools_desc,
        tools_used_note=tools_used_note,
    )

    user_message = f"User query: {query}"
    if context:
        user_message += f"\n\nContext from previous steps:\n{context}"

    response = call_llm(system_prompt=system_prompt, user_message=user_message)
    logger.info(f"Planner raw response: {response}")

    # Parse JSON from the LLM response
    try:
        # Try to extract JSON from the response in case of extra text
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            plan_result = json.loads(json_match.group())
        else:
            plan_result = json.loads(response)
    except json.JSONDecodeError:
        logger.warning("Planner returned invalid JSON, defaulting to respond")
        plan_result = {"action": "respond"}

    # Validate the plan
    if plan_result.get("action") not in ("use_tool", "respond"):
        plan_result = {"action": "respond"}

    return plan_result
