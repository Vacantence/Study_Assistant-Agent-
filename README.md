# AI 学习助手 · AI Study Assistant

[![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-19-blue?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Tauri](https://img.shields.io/badge/Tauri-2.11+-purple?logo=tauri)](https://tauri.app)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> 基于 LLM Agent 的个性化学习助手桌面应用 —— 对话式学习、知识管理、间隔重复复习、知识图谱可视化。

---

## 架构

```
┌──────────────────────────────────────────────────┐
│              Tauri Desktop App                    │
│  ┌────────────────────────────────────────────┐   │
│  │         React + Tailwind CSS UI            │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │   │
│  │  │ 对话  │ │ 资料库 │ │ 复习 │ │ 知识图谱  │  │   │
│  │  └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘  │   │
│  └─────┼────────┼────────┼───────────┼────────┘   │
│        │  HTTP  │        │           │            │
│  ┌─────▼────────▼────────▼───────────▼────────┐   │
│  │           FastAPI Backend (Sidecar)         │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │   │
│  │  │ Agent │ │ 缓存  │ │ 搜索  │ │ 数据库   │  │   │
│  │  └──────┘ └──────┘ └──────┘ └──────────┘  │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

**工作流程：**
```
用户提问 → Agent 接收 → ①查询本地缓存 → ②检索上传文档
→ ③信息不足则联网搜索+网页抓取 → 综合回答
→ ④生成复习卡片(SM-2) → ⑤更新知识图谱
```

---

## 功能

| 功能 | 说明 |
|------|------|
| **对话式学习** | 基于 DeepSeek LLM + LangChain Agent，支持多轮上下文 |
| **知识缓存** | 自动缓存 Q&A，相似问题直接命中，减少 API 调用 |
| **文档 RAG** | 上传 PDF/Word/TXT，自动切片+向量化，检索增强生成 |
| **联网搜索** | Bing 搜索 + 网页正文抓取，补充实时信息 |
| **间隔重复复习** | SM-2 算法，自动安排复习计划，巩固长期记忆 |
| **知识图谱** | 从对话中提取概念关系，vis-network 可视化 |
| **用户记忆** | 记录偏好、兴趣领域、学习进度，个性化回答 |
| **学习文档导出** | Agent 自动生成 Markdown 学习笔记 |
| **多用户** | 注册/登录，独立对话历史和知识库 |
| **REST API** | FastAPI 接口，JWT 认证，支持第三方集成 |

---

## 技术栈

| 层面 | 技术 |
|------|------|
| 桌面壳 | Tauri 2 (Rust) |
| 前端 | React 19 + TypeScript + Tailwind CSS 4 |
| 状态管理 | Zustand |
| 路由 | React Router 7 |
| 后端 API | FastAPI + Uvicorn |
| LLM | DeepSeek Chat (langchain-openai) |
| Embedding | 阿里云 DashScope text-embedding-v3 |
| Agent 框架 | LangChain (create_agent) |
| 搜索 | Bing (HTML scraping) |
| 网页抓取 | Trafilatura |
| 数据库 | SQLite |
| 文档解析 | pypdf, python-docx |
| 向量计算 | NumPy |
| 认证 | JWT (python-jose) |
| 可视化 | vis-network |
| 打包部署 | PyInstaller / Tauri bundler |

---

## 快速开始

### 前置要求

- Python 3.14+
- Node.js 20+
- Rust 1.77+ (仅构建 Tauri 时需要)
- DeepSeek API Key（[申请](https://platform.deepseek.com)）
- 阿里云 DashScope API Key（[申请](https://dashscope.aliyun.com)）— 用于 Embedding

### 本地运行（开发模式）

```bash
# 1. 克隆
git clone https://github.com/yourname/study-assistant
cd study-assistant

# 2. 环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 3. Python 依赖
pip install -r requirements.txt

# 4. 启动后端 API
python run_api.py

# 5. 新终端，启动前端
cd frontend
npm install
npm run dev
```

打开浏览器访问 `http://localhost:5173`

### Tauri 桌面应用

```bash
# 构建桌面应用
cd frontend
npm install
npm run tauri build
```

构建产物在 `frontend/src-tauri/target/release/bundle/`

---

## 项目结构

```
study-assistant/
├── run_api.py                  # FastAPI 后端入口
├── requirements.txt            # Python 依赖
├── build_tauri.bat             # Windows Tauri 构建脚本
├── src/
│   ├── agent_setup.py          # LangChain Agent 构建
│   ├── config.py               # 全局配置
│   ├── api/
│   │   ├── main.py             # FastAPI 应用
│   │   ├── auth.py             # JWT 认证
│   │   └── routes.py           # API 路由
│   ├── knowledge_cache/
│   │   ├── database.py         # SQLite 数据层
│   │   └── embeddings.py       # Embedding 管理
│   └── tools/
│       ├── search.py           # Bing 搜索工具
│       ├── crawler.py          # 网页抓取工具
│       ├── document.py         # 文档生成工具
│       ├── document_loader.py  # 文档解析
│       └── export.py           # 导出工具
├── frontend/
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   ├── components/         # UI 组件
│   │   ├── pages/              # 页面
│   │   ├── stores/             # Zustand 状态
│   │   ├── types/              # TypeScript 类型
│   │   └── config/             # 前端配置
│   └── src-tauri/              # Tauri 配置
│       ├── src/lib.rs          # Rust 逻辑 (后端进程管理)
│       ├── tauri.conf.json
│       └── backend/            # 嵌入的 Python 后端
├── .env.example
└── Dockerfile
```

---

## API 文档

API 服务启动后访问 `http://localhost:8000/docs` 查看 Swagger UI。

### 端点概览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册 | 否 |
| POST | `/api/auth/login` | 登录 | 否 |
| GET | `/api/conversations` | 对话列表 | JWT |
| GET | `/api/chat/stream` | SSE 流式对话 | JWT |
| GET | `/api/review/cards` | 待复习卡片 | JWT |
| POST | `/api/review/cards/{id}/review` | 提交复习评分 | JWT |
| GET | `/api/graph` | 知识图谱数据 | JWT |
| GET | `/api/documents` | 文档列表 | JWT |
| POST | `/api/documents/upload` | 上传文档 | JWT |
| GET | `/api/memory` | 用户记忆 | JWT |
| GET | `/api/cache` | 知识库缓存 | JWT |
| GET | `/api/stats` | 统计数据 | JWT |

---

## 配置

核心配置项在 `src/config.py`，可通过环境变量覆盖：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `CACHE_DB_PATH` | `knowledge_cache.db` | SQLite 数据库路径 |
| `CACHE_SIMILARITY_THRESHOLD` | `0.85` | 缓存命中相似度阈值 |
| `SEARCH_TOP_K` | `5` | 搜索返回结果数 |
| `REVIEW_CARDS_PER_CONVERSATION` | `5` | 每次对话生成的卡片数 |
| `GRAPH_MAX_NODES` | `50` | 知识图谱最大节点数 |
| `MAX_HISTORY_PAIRS` | `15` | 保留的最近对话轮数 |
