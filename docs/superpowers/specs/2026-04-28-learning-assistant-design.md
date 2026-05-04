# LLM 个人学习助手 — 设计文档

## 概述

基于 LLM 的个人学习助手系统。用户提问后，系统自动联网搜索、抓取网页内容、整理总结，最终生成结构化学习文档（Markdown / Word）。

## 技术栈

| 层面 | 选型 |
|------|------|
| LLM | DeepSeek API |
| Agent 框架 | LangChain (ReAct) |
| 前端 | Streamlit |
| 搜索 | DuckDuckGo (duckduckgo_search) |
| 网页抓取 | trafilatura |
| 文档生成 | python-docx + Markdown |
| 知识缓存 | SQLite + sentence-transformers |
| 部署 | 本地 Windows 运行 |

## 系统架构

```
Streamlit UI
    │
    ▼
LangChain Agent (ReAct 循环)
    │
    ├── query_cache      → SQLite + 向量检索
    ├── save_to_cache    → 质量过滤后写入
    ├── search_web       → DuckDuckGo
    ├── scrape_page      → trafilatura
    ├── summarize        → DeepSeek API
    └── generate_doc     → .md / .docx
```

## 缓存控制策略

1. **查重去重**：存储前向量相似度检查（cosine > 0.85 视为重复，跳过存储）
2. **质量过滤**：Agent 判断内容是否充足、相关才缓存
3. **用户可配置**：智能缓存(默认) / 手动确认 / 仅查询不存储 / 清空缓存

## Agent 行为流程

1. 用户提问 → Agent 接收问题
2. 优先查缓存（query_cache）
3. 缓存命中 → 直接生成文档返回
4. 缓存未命中 → search_web → scrape_page → 多个结果汇总
5. LLM 总结归纳 → 结构化学习笔记
6. 质量判断 → 达标则 save_to_cache
7. generate_doc → 返回文件给用户

## 项目结构

```
study-assistant/
├── app.py                    # Streamlit 入口
├── requirements.txt
├── .env
├── src/
│   ├── __init__.py
│   ├── agent_setup.py        # LangChain Agent 配置
│   ├── config.py             # 全局配置
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── crawler.py
│   │   ├── summarizer.py
│   │   └── document.py
│   └── knowledge_cache/
│       ├── __init__.py
│       ├── database.py
│       └── embeddings.py
├── outputs/
└── docs/superpowers/specs/
```

## 各工具模块

### search.py
- 工具名: `search_web`
- 输入: 查询词
- 过程: DuckDuckGo 搜索，取前 5 条
- 输出: `[{"title", "url", "snippet"}]`

### crawler.py
- 工具名: `scrape_page`
- 输入: URL
- 过程: `trafilatura` 提取正文
- 输出: `{"title", "content", "url"}`
- 超时 10s

### summarizer.py
- Agent 在思考步骤中直接调用 LLM 完成
- 输出格式: Markdown 结构化笔记（标题、核心概念、关键细节、总结）

### document.py
- 工具名: `generate_doc`
- 输入: (内容, 格式: md/docx)
- 输出: 文件路径
- 文件名: `{YYYY-MM-DD}_{关键词}.{md|docx}`

### knowledge_cache/
- `database.py`: SQLite 建表、CRUD、查重
- `embeddings.py`: DeepSeek API 生成嵌入向量 + cosine 相似度检索
