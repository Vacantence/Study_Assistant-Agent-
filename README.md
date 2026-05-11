# AI 学习助手 · AI Study Assistant

[![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-19-blue?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Tauri](https://img.shields.io/badge/Tauri-2.11+-purple?logo=tauri)](https://tauri.app)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> 基于 LLM Agent 的个性化学习助手桌面应用 —— 对话式学习、知识管理、间隔重复复习、知识图谱可视化。

---

## 截图

![对话界面](screenshots/chat.png)
![复习卡片](screenshots/review.png)
![知识图谱](screenshots/graph.png)

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
│  │        FastAPI Backend (sidecar进程)        │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │   │
│  │  │ Agent │ │ 缓存  │ │ 搜索  │ │  数据库   │  │   │
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
| **对话式学习** | 基于 LLM Agent，支持多轮上下文 |
| **多 LLM 提供商** | 支持 DeepSeek、OpenAI、智谱等多种兼容 OpenAI API 的模型，可在设置中自由切换 |
| **知识缓存** | 自动缓存 Q&A，相似问题直接命中，减少 API 调用 |
| **文档 RAG** | 上传 PDF/Word/TXT，自动切片+向量化，检索增强生成 |
| **联网搜索** | Bing 搜索 + 网页正文抓取，补充实时信息 |
| **间隔重复复习** | SM-2 算法，自动安排复习计划，巩固长期记忆 |
| **知识图谱** | 从对话中提取概念关系，vis-network 可视化 |
| **用户记忆** | 记录偏好、兴趣领域、学习进度，个性化回答 |
| **学习文档导出** | Agent 自动生成 Markdown 学习笔记 |
| **多用户** | 注册/登录，独立对话历史和知识库 |
| **REST API** | FastAPI 接口，JWT 认证，支持第三方集成 |
| **桌面应用** | Tauri 2 打包，原生窗口体验，自动启动后端 |

---

## 技术栈

| 层面 | 技术 |
|------|------|
| 桌面壳 | Tauri 2 (Rust) |
| 前端 | React 19 + TypeScript + Tailwind CSS 4 |
| 状态管理 | Zustand 5 |
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
| 打包构建 | Tauri bundler |

---

## 快速开始

### 前置要求

- Python 3.14+
- Node.js 20+
- Rust 1.77+（仅构建 Tauri 时需要）
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
cd frontend
npm install
npm run tauri build
```

构建产物在 `frontend/src-tauri/target/release/bundle/`，包含 MSI 和 NSIS 安装包。

### 分发给其他电脑

安装包（MSI/NSIS）只包含 Tauri 桌面壳和 Python 源码，**不包含 Python 解释器和依赖**。在其他电脑上使用需要：

```bash
# 1. 安装 Python 3.14+（勾选 "Add Python to PATH"）
# 2. 安装 Tauri 应用（双击 MSI 或 NSIS 安装包）
# 3. 在项目目录运行一键安装脚本（安装依赖 + 配置环境）
setup.bat

# 4. 启动后端
python run_api.py

# 5. 打开 Tauri 桌面应用
```

**setup.bat** 会自动完成：
- 检测 Python 版本
- 安装 `requirements.txt` 中的所有依赖
- 从 `.env.example` 创建 `.env`（如不存在）
- 创建必要的目录

> 如果只想用浏览器访问，启动后端后访问 `http://localhost:8000` 即可看到 API 文档。

---

## 项目结构

```
study-assistant/
├── run_api.py                  # FastAPI 后端入口
├── run_api.bat                 # Windows 一键启动后端
├── setup.bat                   # 环境安装脚本（给新电脑用）
├── requirements.txt            # Python 依赖
├── build_tauri.bat             # Windows Tauri 构建脚本
├── .env.example                # 环境变量模板
├── src/                        # Python 后端源码
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
├── frontend/                   # React + Tauri 前端
│   ├── src/
│   │   ├── api/                # API 客户端封装
│   │   ├── components/         # UI 组件
│   │   ├── pages/              # 页面（Auth, Chat, Review, Graph, Documents）
│   │   ├── stores/             # Zustand 状态管理
│   │   ├── types/              # TypeScript 类型定义
│   │   └── config/             # 前端配置
│   └── src-tauri/              # Tauri 配置与 Rust 源码
│       ├── src/lib.rs          # Rust 逻辑（后端进程管理）
│       ├── build.rs            # 构建脚本（嵌入后端文件）
│       ├── backend/            # 嵌入的 Python 后端副本
│       └── tauri.conf.json     # Tauri 配置
├── Dockerfile
├── docker-compose.yml
└── README.md
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
| GET | `/api/conversations/{id}/messages` | 对话消息 | JWT |
| GET | `/api/chat/stream` | SSE 流式对话 | JWT |
| POST | `/api/chat` | 非流式对话 | JWT |
| GET | `/api/review/cards` | 待复习卡片 | JWT |
| POST | `/api/review/cards/{id}/review` | 提交复习评分 | JWT |
| DELETE | `/api/review/cards/{id}` | 删除复习卡片 | JWT |
| GET | `/api/graph` | 知识图谱数据 | JWT |
| DELETE | `/api/graph` | 清空知识图谱 | JWT |
| GET | `/api/documents` | 文档列表 | JWT |
| POST | `/api/documents/upload` | 上传文档 | JWT |
| DELETE | `/api/documents/{id}` | 删除文档 | JWT |
| GET | `/api/memory` | 用户记忆 | JWT |
| GET | `/api/cache` | 知识库缓存列表 | JWT |
| GET | `/api/llm/providers` | 获取 LLM 提供商列表 | JWT |
| GET | `/api/llm/providers/active` | 获取当前活跃的 LLM 提供商 | JWT |
| POST | `/api/llm/providers` | 添加 LLM 提供商 | JWT |
| PUT | `/api/llm/providers/{id}` | 编辑 LLM 提供商 | JWT |
| POST | `/api/llm/providers/{id}/activate` | 切换活跃提供商 | JWT |
| DELETE | `/api/llm/providers/{id}` | 删除 LLM 提供商 | JWT |
| GET | `/api/stats` | 统计数据 | JWT |

---

## 配置

核心配置项在 `src/config.py`，可通过环境变量覆盖：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `CACHE_DB_PATH` | `knowledge_cache.db` | SQLite 数据库路径 |
| `CACHE_SIMILARITY_THRESHOLD` | `0.85` | 缓存命中相似度阈值 |
| `CACHE_MODE` | `auto` | 缓存模式（auto/manual/query_only）|
| `SEARCH_TOP_K` | `5` | 搜索返回结果数 |
| `REVIEW_CARDS_PER_CONVERSATION` | `5` | 每次对话生成的卡片数 |
| `GRAPH_MAX_NODES` | `50` | 知识图谱最大节点数 |
| `MAX_HISTORY_PAIRS` | `15` | 保留的最近对话轮数 |
| `SM2_DEFAULT_EASINESS` | `2.5` | SM-2 默认轻松度 |
| `SM2_MIN_EASINESS` | `1.3` | SM-2 最低轻松度 |
| `JWT_EXPIRATION_HOURS` | `72` | JWT 过期时间 |

### 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API Key |
| `ALIYUN_EMBEDDING_API_KEY` | 否 | 阿里云 DashScope Key（有默认测试值）|
| `JWT_SECRET` | 否 | JWT 签名密钥（有默认值，生产环境请修改）|

---

## 截图

> TODO: 添加截图

将截图放在 `screenshots/` 目录下，命名为 `chat.png`、`review.png`、`graph.png`。
