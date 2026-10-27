from langchain_tavily import TavilySearch

from app.config import TAVILY_API_KEY


web_search = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="basic"
)