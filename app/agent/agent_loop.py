import logging

from app.agent.executor import Executor
from app.agent.planner import plan
from app.services.llm import call_llm
from app.services.prompt_builder import build_final_prompt
from app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3


def run_agent(query: str, tools: list[BaseTool]) -> dict:
    """Run the agent loop for a given user query.

    Returns a dict with:
        answer: final response string
        steps: list of intermediate steps for transparency
    """
    executor = Executor(tools)
    steps: list[dict] = []
    context = ""

    for iteration in range(1, MAX_ITERATIONS + 1):
        logger.info(f"--- Agent loop iteration {iteration} ---")

        # Step 1: Plan
        plan_result = plan(query, tools, context)
        steps.append({"iteration": iteration, "plan": plan_result})
        logger.info(f"Plan result: {plan_result}")

        # Step 2: If direct response, generate answer
        if plan_result["action"] == "respond":
            answer = _generate_final_answer(query, context)
            steps.append({"iteration": iteration, "final_answer": True})
            return {"answer": answer, "steps": steps}

        # Step 3: Execute tool
        tool_name = plan_result.get("tool_name", "")
        parameters = plan_result.get("parameters", "")
        tool_result = executor.run(tool_name, parameters)
        steps.append({
            "iteration": iteration,
            "tool_used": tool_name,
            "tool_input": parameters,
            "tool_output": tool_result,
        })

        # Append result to context for next iteration
        context += f"\nTool '{tool_name}' was called with input '{parameters}' and returned: {tool_result}\n"

    # If we exhausted iterations, generate a final answer with whatever context we have
    logger.warning("Max iterations reached, generating final answer with available context")
    answer = _generate_final_answer(query, context)
    steps.append({"final_answer": True, "reason": "max_iterations_reached"})
    return {"answer": answer, "steps": steps}


def _generate_final_answer(query: str, context: str) -> str:
    """Generate the final answer using the LLM."""
    system_prompt, user_message = build_final_prompt(query, context)
    return call_llm(system_prompt=system_prompt, user_message=user_message)
