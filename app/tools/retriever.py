import json
from pathlib import Path

from app.tools.base_tool import BaseTool

# Simple in-memory document store for demonstration.
# In production, this would connect to a vector DB or RAG pipeline.
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_documents() -> list[dict]:
    """Load documents from a JSON file if available."""
    docs_file = _DATA_DIR / "documents.json"
    if docs_file.exists():
        with open(docs_file) as f:
            return json.load(f)
    return []


def _simple_search(query: str, documents: list[dict], top_k: int = 3) -> list[str]:
    """Simple keyword-based retrieval (placeholder for vector search)."""
    query_terms = set(query.lower().split())
    scored = []
    for doc in documents:
        content = doc.get("content", "")
        doc_terms = set(content.lower().split())
        overlap = len(query_terms & doc_terms)
        if overlap > 0:
            scored.append((overlap, content))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:top_k]]


class RetrieverTool(BaseTool):
    name = "retriever"
    description = "Retrieves relevant document chunks based on a query. Use this when the user asks about information in stored documents."

    def execute(self, input_data: str) -> str:
        documents = _load_documents()
        if not documents:
            return "No documents available in the knowledge base."
        results = _simple_search(input_data, documents)
        if not results:
            return "No relevant documents found for the query."
        return "\n\n---\n\n".join(results)
