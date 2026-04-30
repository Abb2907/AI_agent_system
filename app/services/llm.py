import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client: OpenAI | None = None

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set. Get a free key at https://console.groq.com")
        _client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    return _client


def call_llm(system_prompt: str, user_message: str, model: str | None = None) -> str:
    """Call the Groq chat completion API and return the assistant's response."""
    model = model or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    client = _get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""
