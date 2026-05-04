from langchain.tools import tool
import trafilatura
import requests


@tool
def scrape_page(url: str) -> dict:
    """抓取指定 URL 的网页正文内容。输入必须是完整的 URL（包含 https://）。"""
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36")
        })
        response.raise_for_status()

        extracted = trafilatura.bare_extraction(
            response.text,
            include_links=False,
            include_images=False,
            include_tables=True,
        )
        if not extracted:
            return {"error": "无法提取网页正文", "url": url}

        return {
            "title": extracted.get("title", ""),
            "content": extracted.get("text", ""),
            "url": url,
        }
    except Exception as e:
        return {"error": str(e), "url": url}
