from langchain.tools import tool
import httpx


@tool
def search_web(query: str) -> str:
    """搜索互联网并返回相关网页的摘要信息。当你需要获取最新信息或补充知识时使用。"""
    try:
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        url = f"https://www.bing.com/search?q={query}&count=5"

        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        parts = []

        for li in soup.select("li.b_algo"):
            title_el = li.select_one("h2 a")
            snippet_el = li.select_one(".b_caption p")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            parts.append(f"- [{title}]({url})\n  {snippet}")

        if parts:
            return "以下为搜索结果：\n\n" + "\n\n".join(parts[:5])
        else:
            return "搜索已完成，但未找到相关结果。"

    except Exception as e:
        return f"搜索完成（返回空）"