def build_final_prompt(query: str, context: str) -> tuple[str, str]:
    """Build the system prompt and user message for final answer generation.

    Returns:
        A tuple of (system_prompt, user_message).
    """
    system_prompt = (
        "You are a helpful AI assistant. Generate a clear, concise final answer "
        "to the user's question. If tool results are provided in the context, "
        "incorporate them into your answer and briefly explain what was done."
    )

    user_message = f"Question: {query}"
    if context.strip():
        user_message += f"\n\nContext (tool results and reasoning):\n{context}"
    user_message += "\n\nProvide a clear and helpful answer."

    return system_prompt, user_message
