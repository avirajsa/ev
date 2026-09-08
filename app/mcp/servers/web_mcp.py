import logging
import httpx
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger("ev.mcp.web")

class WebMCPServer:
    """
    100% Free Web Search & Web Scraping MCP Server.
    Uses DuckDuckGo Search (no API key required) and BeautifulSoup HTML parsing.
    """

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_duckduckgo",
                "description": "Performs a free web search via DuckDuckGo and returns top results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or question"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of search results (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch_webpage_content",
                "description": "Fetches and extracts clean text content from a web URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Public web URL to fetch"
                        }
                    },
                    "required": ["url"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[WebMCP] Executing tool '{tool_name}' with args: {arguments}")

        if tool_name == "search_duckduckgo":
            query = arguments.get("query")
            max_results = arguments.get("max_results", 5)
            try:
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append({
                            "title": r.get("title"),
                            "snippet": r.get("body"),
                            "url": r.get("href")
                        })
                return {"query": query, "results": results}
            except Exception as e:
                logger.error(f"[WebMCP] DuckDuckGo search error: {e}")
                return {"error": f"Search failed: {str(e)}"}

        elif tool_name == "fetch_webpage_content":
            url = arguments.get("url")
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EV-AI-Assistant/1.0"}
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                
                if resp.status_code != 200:
                    return {"error": f"HTTP {resp.status_code} fetching URL"}

                soup = BeautifulSoup(resp.text, "html.parser")
                # Remove scripts, styles
                for element in soup(["script", "style", "nav", "footer"]):
                    element.decompose()

                text = soup.get_text(separator=" ", strip=True)
                # Truncate text to 10k chars
                truncated_text = text[:10000]
                return {
                    "url": url,
                    "title": soup.title.string if soup.title else "No Title",
                    "content": truncated_text
                }
            except Exception as e:
                logger.error(f"[WebMCP] Fetch webpage error: {e}")
                return {"error": f"Failed fetching URL: {str(e)}"}

        return {"error": f"Unknown tool: {tool_name}"}

web_mcp_server = WebMCPServer()
