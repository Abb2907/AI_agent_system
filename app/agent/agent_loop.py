import logging
import time

from app.agent.executor import Executor
from app.agent.planner import plan
from app.services.llm import call_llm
from app.services.prompt_builder import build_final_prompt
from app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5  # Increased for tool chaining


def run_agent(
    query: str,
    tools: list[BaseTool],
    history: list[dict] | None = None,
) -> dict:
    """Run the agent loop for a given user query with tool chaining support.

    Args:
        query: The user's question/request
        tools: Available tools for the agent
        history: Previous conversation messages for context

    Returns a dict with:
        answer: final response string
        steps: list of intermediate steps for transparency
    """
    agent_start = time.time()
    executor = Executor(tools)
    steps: list[dict] = []
    context = ""

    # Incorporate conversation history into context
    if history:
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-10:]
        )
        context += f"Previous conversation:\n{history_text}\n\n"

    tools_used: list[str] = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        logger.info(f"--- Agent loop iteration {iteration} ---")

        # Step 1: Plan (with awareness of tools already used)
        plan_start = time.time()
        plan_result = plan(query, tools, context, tools_used=tools_used)
        plan_duration = round(time.time() - plan_start, 2)

        steps.append({
            "type": "thinking",
            "iteration": iteration,
            "plan": plan_result,
            "duration_s": plan_duration,
        })
        logger.info(f"Plan result ({plan_duration}s): {plan_result}")

        # Step 2: If direct response, generate answer
        if plan_result["action"] == "respond":
            gen_start = time.time()
            answer = _generate_final_answer(query, context)
            gen_duration = round(time.time() - gen_start, 2)
            total_duration = round(time.time() - agent_start, 2)

            steps.append({
                "type": "answer",
                "iteration": iteration,
                "duration_s": gen_duration,
                "total_duration_s": total_duration,
            })
            return {"answer": answer, "steps": steps}

        # Step 3: Execute tool (supports chaining)
        tool_name = plan_result.get("tool_name", "")
        parameters = plan_result.get("parameters", "")

        logger.info(f"Tool chain step {iteration}: {tool_name}")
        exec_start = time.time()
        tool_result = executor.run(tool_name, parameters)
        exec_duration = round(time.time() - exec_start, 2)
        tools_used.append(tool_name)

        steps.append({
            "type": "tool",
            "iteration": iteration,
            "tool_name": tool_name,
            "tool_input": parameters,
            "tool_output": tool_result,
            "duration_s": exec_duration,
        })

        # Append result to context for next iteration (enables chaining)
        context += f"\nTool '{tool_name}' was called with input '{parameters}' and returned: {tool_result}\n"

    # If we exhausted iterations, generate a final answer with whatever context we have
    logger.warning("Max iterations reached, generating final answer with available context")
    answer = _generate_final_answer(query, context)
    total_duration = round(time.time() - agent_start, 2)
    steps.append({
        "type": "answer",
        "reason": "max_iterations_reached",
        "total_duration_s": total_duration,
    })
    return {"answer": answer, "steps": steps}


def _generate_final_answer(query: str, context: str) -> str:
    """Generate the final answer using the LLM."""
    system_prompt, user_message = build_final_prompt(query, context)
    return call_llm(system_prompt=system_prompt, user_message=user_message)

