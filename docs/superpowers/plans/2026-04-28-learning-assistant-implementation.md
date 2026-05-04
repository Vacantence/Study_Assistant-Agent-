# LLM 个人学习助手 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 DeepSeek + LangChain 的个人学习助手，支持联网搜索、网页抓取、知识缓存和文档生成

**Architecture:** Streamlit 前端 → LangChain ReAct Agent → 5 个工具模块（缓存查询/搜索/抓取/总结/文档生成）+ SQLite 知识缓存

**Tech Stack:** Python, LangChain, Streamlit, DeepSeek API, duckduckgo_search, trafilatura, python-docx, SQLite, sentence-transformers

---

### Task 1: 项目初始化与依赖管理

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `src/__init__.py`
- Create: `src/tools/__init__.py`
- Create: `src/knowledge_cache/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
# requirements.txt
streamlit>=1.28.0
langchain>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.2.0
duckduckgo-search>=6.0.0
trafilatura>=1.6.0
python-docx>=1.1.0
sentence-transformers>=3.0.0
openai>=1.0.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: 创建 .env 文件**

```txt
DEEPSEEK_API_KEY=your_api_key_here
```

- [ ] **Step 3: 创建包初始化文件**

```python
# src/__init__.py
```

```python
# src/tools/__init__.py
```

```python
# src/knowledge_cache/__init__.py
```

- [ ] **Step 4: 创建虚拟环境并安装依赖**

Run:
```bash
cd D:/VScode/Agent/Study_Assistant
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

---

### Task 2: 配置模块

**Files:**
- Create: `src/config.py`

- [ ] **Step 1: 创建配置类**

```python
# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-chat"
    DEEPSEEK_EMBEDDING_MODEL = "deepseek-chat"  # 使用 chat 模型生成嵌入

    # 知识缓存配置
    CACHE_DB_PATH = "knowledge_cache.db"
    CACHE_SIMILARITY_THRESHOLD = 0.85
    CACHE_MODE = "auto"  # auto | manual | query_only

    # 搜索配置
    SEARCH_TOP_K = 5

    # 文档配置
    OUTPUT_DIR = "outputs"
```

---

### Task 3: 知识缓存 — 数据库层

**Files:**
- Create: `src/knowledge_cache/database.py`

- [ ] **Step 1: 创建 SQLite 数据库管理类**

```python
# src/knowledge_cache/database.py
import sqlite3
import json
from datetime import datetime
from typing import Optional
from src.config import Config


class CacheDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.CACHE_DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    sources TEXT NOT NULL,  -- JSON array of URLs
                    embedding BLOB,
                    quality_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_query ON knowledge_cache(query)
            """)

    def save(self, query: str, summary: str, sources: list[str],
             embedding: bytes = None, quality_score: float = 0.0) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO knowledge_cache
                   (query, summary, sources, embedding, quality_score, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (query, summary, json.dumps(sources),
                 embedding, quality_score, datetime.now().isoformat())
            )
            return cur.lastrowid

    def get_all_with_embeddings(self) -> list[dict]:
        """返回所有缓存的记录（含 embedding 字段），供上层做向量相似度匹配"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM knowledge_cache ORDER BY quality_score DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_by_query(self, query: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM knowledge_cache WHERE query = ?", (query,)
            ).fetchone()
            return dict(row) if row else None

    def increment_access(self, cache_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE knowledge_cache SET access_count = access_count + 1 WHERE id = ?",
                (cache_id,)
            )

    def get_all(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, query, created_at, quality_score, access_count FROM knowledge_cache ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def delete(self, cache_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM knowledge_cache WHERE id = ?", (cache_id,))

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM knowledge_cache")
```

---

### Task 4: 知识缓存 — 嵌入向量与检索

**Files:**
- Create: `src/knowledge_cache/embeddings.py`

- [ ] **Step 1: 创建嵌入向量管理器**

```python
# src/knowledge_cache/embeddings.py
import numpy as np
from openai import OpenAI
from src.config import Config


class EmbeddingManager:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_API_BASE,
        )

    def embed_text(self, text: str) -> list[float]:
        """使用 DeepSeek API 生成文本嵌入向量"""
        response = self.client.embeddings.create(
            model="deepseek-chat",
            input=text[:2048],  # 截断过长文本
        )
        return response.data[0].embedding

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def find_best_match(self, query: str, records: list[dict],
                        threshold: float = None) -> tuple[dict | None, float]:
        """在缓存记录中找到最匹配的条目"""
        threshold = threshold or Config.CACHE_SIMILARITY_THRESHOLD
        query_emb = self.embed_text(query)
        best_score = 0.0
        best_record = None

        for record in records:
            stored_emb = record.get("embedding")
            if stored_emb:
                stored_vec = np.frombuffer(stored_emb, dtype=np.float32).tolist()
                score = self.cosine_similarity(query_emb, stored_vec)
                if score > best_score:
                    best_score = score
                    best_record = record

        if best_score >= threshold:
            return best_record, best_score
        return None, best_score
```

---

### Task 5: 搜索工具

**Files:**
- Create: `src/tools/search.py`

- [ ] **Step 1: 创建 DuckDuckGo 搜索工具**

```python
# src/tools/search.py
from langchain.tools import tool
from duckduckgo_search import DDGS
from src.config import Config


@tool
def search_web(query: str) -> list[dict]:
    """搜索互联网并返回相关网页列表。当你需要获取最新信息或补充知识时使用。"""
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
```

---

### Task 6: 网页抓取工具

**Files:**
- Create: `src/tools/crawler.py`

- [ ] **Step 1: 创建网页正文提取工具**

```python
# src/tools/crawler.py
from langchain.tools import tool
import trafilatura
import requests


@tool
def scrape_page(url: str) -> dict:
    """抓取指定 URL 的网页正文内容。输入必须是完整的 URL（包含 https://）。"""
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })
        response.raise_for_status()

        # 提取元数据
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
```

---

### Task 7: 文档生成工具

**Files:**
- Create: `src/tools/document.py`

- [ ] **Step 1: 创建文档生成工具**

```python
# src/tools/document.py
import os
from datetime import datetime
from langchain.tools import tool
from docx import Document
from docx.shared import Pt, Inches
from src.config import Config


def _sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name)[:50]


def _generate_markdown(content: str, topic: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{_sanitize_filename(topic)}.md"
    filepath = os.path.join(Config.OUTPUT_DIR, filename)
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n")
        f.write(f"> 生成日期: {date_str}\n\n")
        f.write(content)

    return filepath


def _generate_docx(content: str, topic: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{_sanitize_filename(topic)}.docx"
    filepath = os.path.join(Config.OUTPUT_DIR, filename)
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    doc = Document()
    doc.add_heading(topic, 0)
    doc.add_paragraph(f"生成日期: {date_str}")

    for line in content.split("\n"):
        if line.startswith("## "):
            doc.add_heading(line.strip("# "), 2)
        elif line.startswith("### "):
            doc.add_heading(line.strip("# "), 3)
        elif line.startswith("- "):
            doc.add_paragraph(line, style="List Bullet")
        elif line.strip():
            doc.add_paragraph(line)

    doc.save(filepath)
    return filepath


@tool
def generate_doc(content: str, topic: str, fmt: str = "md") -> str:
    """将整理好的学习内容生成文档。fmt 支持 'md'(Markdown) 或 'docx'(Word)。"""
    if fmt == "docx":
        return _generate_docx(content, topic)
    return _generate_markdown(content, topic)
```

---

### Task 8: Agent 设置

**Files:**
- Create: `src/agent_setup.py`

- [ ] **Step 1: 创建 Agent 初始化模块**

```python
# src/agent_setup.py
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from src.config import Config
from src.tools.search import search_web
from src.tools.crawler import scrape_page
from src.tools.document import generate_doc
from src.knowledge_cache.database import CacheDatabase
from src.knowledge_cache.embeddings import EmbeddingManager


# 将缓存查询包装为 LangChain Tool
def _query_cache_wrapper(query: str) -> str:
    db = CacheDatabase()
    emb = EmbeddingManager()
    records = db.get_all_with_embeddings()  # 获取所有记录
    if not records:
        return "缓存为空"

    match, score = emb.find_best_match(query, records)
    if match:
        db.increment_access(match["id"])
        return f"【缓存命中 (相似度: {score:.2f})】\n{match['summary']}\n来源: {match['sources']}"
    return "缓存未命中"


def _save_cache_wrapper(input_str: str) -> str:
    """输入格式: 查询词 ||| 总结内容 ||| 来源URL(逗号分隔)"""
    try:
        parts = input_str.split("|||")
        query = parts[0].strip()
        summary = parts[1].strip()
        sources = [s.strip() for s in parts[2].split(",")] if len(parts) > 2 else []

        db = CacheDatabase()
        emb = EmbeddingManager()

        # 再次查重
        records = db.get_all_with_embeddings()
        if records:
            _, score = emb.find_best_match(query, records)
            if score >= Config.CACHE_SIMILARITY_THRESHOLD:
                return "跳过存储: 缓存中已有类似内容"

        # 生成向量嵌入
        embedding_vec = emb.embed_text(query + " " + summary)
        embedding_bytes = np.array(embedding_vec, dtype=np.float32).tobytes()

        # 简单质量评分：按内容长度
        quality = min(len(summary) / 500, 1.0)

        db.save(query, summary, sources, embedding_bytes, quality)
        return "已保存到知识缓存"
    except Exception as e:
        return f"缓存保存失败: {str(e)}"


query_cache_tool = Tool(
    name="query_cache",
    func=_query_cache_wrapper,
    description="从本地知识缓存中查找已有学习内容。在搜索之前先调用此工具。输入：查询词。"
)

save_cache_tool = Tool(
    name="save_to_cache",
    func=_save_cache_wrapper,
    description="将高质量的学习总结保存到本地知识缓存。输入格式: '查询词 ||| 总结内容 ||| 来源URL1,来源URL2'"
)


def create_agent():
    llm = ChatOpenAI(
        model=Config.DEEPSEEK_MODEL,
        openai_api_key=Config.DEEPSEEK_API_KEY,
        openai_api_base=Config.DEEPSEEK_API_BASE,
        temperature=0.7,
    )

    tools = [
        query_cache_tool,
        save_cache_tool,
        search_web,
        scrape_page,
        generate_doc,
    ]

    prompt = PromptTemplate.from_template("""
你是一个个人学习助手。你的目标是帮助用户深入学习某个知识点。

你的工作流程：
1. 首先调用 query_cache 检查本地知识库是否已有相关内容
2. 如果缓存命中，直接用缓存内容为用户生成学习文档
3. 如果缓存未命中，使用 search_web 搜索互联网，然后用 scrape_page 抓取网页正文
4. 综合所有抓取的内容，用中文进行结构化的总结
5. 如果总结质量高，调用 save_to_cache 保存到知识库
6. 最后调用 generate_doc 生成学习文档
7. 返回文档路径给用户

注意：
- 始终用中文回答
- 总结要结构化，包含：核心概念、关键细节、实际应用
- 对于高质量内容（内容丰富、信息完整），调用 save_to_cache
- 对于内容太少或无关的结果，跳过 save_to_cache

工具:
{tools}

用户问题: {input}

你的思考过程（用中文）:
{agent_scratchpad}
""")

    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )
```

注意：需要在 `agent_setup.py` 顶部加上 `import numpy as np`。

- [ ] **Step 2: 添加缺失的 import**

在 `src/agent_setup.py` 顶部加上：
```python
import numpy as np
```

---

### Task 9: Streamlit 前端

**Files:**
- Create: `app.py`

- [ ] **Step 1: 创建 Streamlit 主界面**

```python
# app.py
import streamlit as st
from src.config import Config
from src.agent_setup import create_agent
from src.knowledge_cache.database import CacheDatabase

st.set_page_config(page_title="AI 学习助手", page_icon="📚", layout="wide")

# 初始化
if "agent" not in st.session_state:
    st.session_state.agent = create_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []


def main():
    st.title("📚 AI 学习助手")
    st.markdown("输入你想学习的问题，我会自动搜索、整理并生成学习文档。")

    # 侧边栏 - 缓存控制
    with st.sidebar:
        st.header("知识库管理")
        db = CacheDatabase()

        cache_mode = st.radio(
            "缓存模式",
            options=["智能缓存 (自动)", "仅查询不存储", "清空知识库"],
            index=0,
            help="智能缓存: 自动判断是否存储; 仅查询: 不写入新内容"
        )

        if cache_mode == "清空知识库":
            if st.button("确认清空"):
                db.clear_all()
                st.success("知识库已清空")
                st.rerun()

        st.divider()
        st.subheader("已缓存的知识")
        records = db.get_all()
        if records:
            for r in records:
                with st.expander(f"{r['query'][:40]}"):
                    st.text(f"质量评分: {r['quality_score']:.2f}")
                    st.text(f"访问次数: {r['access_count']}")
                    st.text(f"创建时间: {r['created_at']}")
                    if st.button("删除", key=f"del_{r['id']}"):
                        db.delete(r["id"])
                        st.rerun()
        else:
            st.info("知识库为空")

        st.divider()
        st.caption(f"模型: {Config.DEEPSEEK_MODEL}")

    # 聊天记录
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "filepath" in msg:
                st.download_button(
                    label="下载文档",
                    data=open(msg["filepath"], "rb").read(),
                    file_name=msg["filepath"].split("/")[-1],
                    mime="text/markdown",
                )

    # 输入
    if prompt := st.chat_input("输入你想学习的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("正在研究... 可能需要一些时间"):
                agent = st.session_state.agent
                result = agent.invoke({"input": prompt})
                response = result["output"]
                st.markdown(response)

                # 查找 outputs 目录中最新的文件
                import os, glob
                output_files = glob.glob(f"{Config.OUTPUT_DIR}/*.md")
                latest_file = max(output_files, key=os.path.getctime) if output_files else None

                if latest_file:
                    with open(latest_file, "rb") as f:
                        st.download_button(
                            label="📥 下载学习文档",
                            data=f,
                            file_name=os.path.basename(latest_file),
                            mime="text/markdown",
                        )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "filepath": latest_file,
                })


if __name__ == "__main__":
    main()
```

---

### Task 10: 创建 outputs 目录

- [ ] **Step 1: 创建 outputs 目录**

```bash
mkdir -p "D:/VScode/Agent/Study_Assistant/outputs"
```

---

### Task 11: 运行验证

- [ ] **Step 1: 启动应用**

```bash
cd D:/VScode/Agent/Study_Assistant
source venv/Scripts/activate
streamlit run app.py
```

- [ ] **Step 2: 输入测试问题**

在打开的浏览器窗口中输入一个测试问题，例如 "什么是Transformer模型"，观察 Agent 是否：
1. 先查询缓存
2. 搜索 DuckDuckGo
3. 抓取网页内容
4. 生成结构化总结
5. 保存到缓存
6. 生成文档文件
