import logging
import re
from typing import List, Dict, Any
from duckduckgo_search import DDGS

logger = logging.getLogger("uvicorn.error")

TEMPORAL_KEYWORDS = [
    "latest", "recent", "current", "news", "today", "yesterday", "this week",
    "this month", "this year", "now", "upcoming", "release date", "update",
    "price of", "stock price", "weather in", "score of", "who is the current",
    "search web", "search internet", "search online", "2025", "2026", "2027"
]

def should_search_web(query: str, has_attached_docs: bool = False) -> bool:
    """
    Decides whether web search is required for the user query.
    - If user explicitly mentions search, returns True.
    - If temporal / real-time / current events keywords match and it's not strictly a doc query, returns True.
    - Otherwise returns False (no search for general knowledge like 'What is Python?').
    """
    if not query:
        return False

    q_lower = query.lower()

    # Explicit instruction always triggers search
    if any(phrase in q_lower for phrase in ["search the web", "search online", "google this", "look up on the web"]):
        return True

    # If asking about uploaded documents specifically, default to RAG rather than web
    if has_attached_docs and any(k in q_lower for k in ["this document", "this file", "the pdf", "my resume", "the doc"]):
        return False

    # Check for temporal or current events keywords
    for keyword in TEMPORAL_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', q_lower):
            return True

    return False

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Executes a web search using DuckDuckGo.
    Returns list of dicts with title, url, snippet.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    try:
        logger.info(f"Performing web search for: '{clean_query}'")
        results = []
        with DDGS() as ddgs:
            try:
                raw_results = list(ddgs.text(clean_query, backend="html", max_results=max_results))
            except Exception:
                raw_results = list(ddgs.text(clean_query, max_results=max_results))

            for item in raw_results:
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", "")
                })
        logger.info(f"Web search found {len(results)} results.")
        return results
    except Exception as e:
        logger.error(f"Error during web search: {e}")
        # Graceful fallback: return empty list without crashing
        return []
