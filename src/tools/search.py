from langchain.tools import tool
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

from src.config import Config


@tool
def search_web(query: str) -> list[dict]:
    """搜索互联网并返回相关网页列表。当你需要获取最新信息或补充知识时使用。"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=Config.SEARCH_TOP_K))
            return [
                {
                    "title": r["title"],
                    "url": r["href"],
                    "snippet": r["body"],
                }
                for r in results
            ]
    except DuckDuckGoSearchException as e:
        return [{"title": f"搜索失败: {str(e)}", "url": "", "snippet": "请稍后重试"}]
