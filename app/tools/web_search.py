import httpx

from app.tools.base_tool import BaseTool

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Searches Wikipedia for information on a topic. Use this when the user asks about real-world facts, people, places, events, or concepts not in the local documents."

    def execute(self, input_data: str) -> str:
        headers = {"User-Agent": "AIAgentSystem/1.0 (Educational Project)"}
        try:
            # First, search for matching pages
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": input_data,
                "srlimit": 3,
                "format": "json",
            }
            with httpx.Client(timeout=10.0, headers=headers) as client:
                resp = client.get(WIKIPEDIA_API, params=search_params)
                resp.raise_for_status()
                data = resp.json()

            results = data.get("query", {}).get("search", [])
            if not results:
                return f"No Wikipedia results found for: {input_data}"

            # Get a summary extract of the top result
            title = results[0]["title"]
            extract_params = {
                "action": "query",
                "titles": title,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "format": "json",
            }
            with httpx.Client(timeout=10.0, headers=headers) as client:
                resp = client.get(WIKIPEDIA_API, params=extract_params)
                resp.raise_for_status()
                data = resp.json()

            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                extract = page.get("extract", "")
                if extract:
                    # Truncate to keep context window manageable
                    if len(extract) > 1000:
                        extract = extract[:1000] + "..."
                    return f"Wikipedia - {title}:\n{extract}"

            return f"Found page '{title}' but no extract available."
        except httpx.HTTPError as e:
            return f"Web search failed: {e}"
        except Exception as e:
            return f"Web search error: {e}"
