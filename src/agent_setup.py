from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool

from src.config import Config
from src.tools.search import search_web
from src.tools.crawler import scrape_page
from src.knowledge_cache.database import CacheDatabase, UserMemoryManager
from src.knowledge_cache.embeddings import EmbeddingManager

BASE_SYSTEM_PROMPT = """你是一个个人学习助手。你的目标是帮助用户深入学习某个知识点。

工作流程：
1. 先调用 query_cache 检查本地知识库
2. 再调用 query_documents 搜索用户上传的教材/文档
3. 如果以上有足够信息，直接回答用户
4. 如果以上不足，使用 search_web 搜索 → scrape_page 抓取 → 综合分析
5. 用中文给出结构化回答，格式：
   - 核心概念
   - 关键细节
   - 实际应用/例子
6. 回答要完整、详细，便于后续生成学习文档
7. 回答完成后，调用 create_review_cards 为本次学习内容生成 5 个复习卡片（传入 topic 和回答内容）
8. 最后调用 update_knowledge_graph 提取本次回答中的关键概念和关系

注意：始终用中文回答。
"""


def build_agent(user_id: int = None):
    # 基础工具
    tools = [
        _query_cache_tool,
        _query_documents_tool,
        search_web,
        scrape_page,
    ]

    # 构建 system prompt，注入用户记忆
    system_prompt = BASE_SYSTEM_PROMPT
    if user_id is not None:
        prompt_extra = []
        mem = UserMemoryManager().format_memory(user_id)
        if mem:
            prompt_extra.append(mem)
            prompt_extra.append(
                "你可以通过 update_memory 工具记录用户偏好，"
                "通过 read_memory 查看已保存的信息。"
            )
        else:
            prompt_extra.append(
                "你可以使用 update_memory 工具记录用户的偏好、兴趣领域、"
                "学习进度等信息，以便日后提供更个性化的帮助。"
            )
        system_prompt += "\n\n" + "\n".join(prompt_extra)
        tools.append(_make_update_memory_tool(user_id))
        tools.append(_make_read_memory_tool(user_id))
        tools.append(_make_create_review_cards_tool(user_id))
        tools.append(_make_update_knowledge_graph_tool(user_id))

    llm = ChatOpenAI(
        model=Config.DEEPSEEK_MODEL,
        openai_api_key=Config.DEEPSEEK_API_KEY,
        openai_api_base=Config.DEEPSEEK_API_BASE,
        temperature=0.7,
    )

    agent = create_agent(
        llm,
        tools,
        system_prompt=system_prompt,
    )
    return agent


# ----- 内置工具 -----

def _query_cache_wrapper(query: str) -> str:
    db = CacheDatabase()
    emb = EmbeddingManager()
    records = db.get_all_with_embeddings()
    if not records:
        return "缓存为空"
    match, score = emb.find_best_match(query, records)
    if match:
        db.increment_access(match["id"])
        return (
            f"【缓存命中 (相似度: {score:.2f})】\n"
            f"{match['summary']}\n来源: {match['sources']}"
        )
    return "缓存未命中"


_query_cache_tool = StructuredTool.from_function(
    name="query_cache",
    func=_query_cache_wrapper,
    description="从本地知识缓存中查找已有学习内容。在搜索之前先调用此工具。输入：查询词。",
)


# ----- 文档检索工具 -----

def _query_documents_wrapper(query: str) -> str:
    import numpy as np
    from src.knowledge_cache.database import DocumentDatabase
    emb = EmbeddingManager()
    chunks = DocumentDatabase().get_all_chunks_with_embeddings()
    if not chunks:
        return "未找到已上传的文档资料"

    query_emb = emb.embed_text(query)
    scored = []
    for c in chunks:
        stored_emb = c.get("embedding")
        if not stored_emb:
            continue
        stored_vec = np.frombuffer(stored_emb, dtype=np.float32).tolist()
        if len(stored_vec) != len(query_emb):
            continue
        score = emb.cosine_similarity(query_emb, stored_vec)
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:3]

    if not top or top[0][0] < 0.7:
        return f"文档库中未找到相关内容（最高相似度: {top[0][0]:.2f}）" if top else "文档库中未找到相关内容"

    results = []
    for score, chunk in top:
        filename = chunk.get("filename", "未知")
        results.append(
            f"【来自《{filename}》 相似度: {score:.2f}】\n{chunk['content'][:500]}"
        )
    return "\n\n---\n\n".join(results)


_query_documents_tool = StructuredTool.from_function(
    name="query_documents",
    func=_query_documents_wrapper,
    description="在用户上传的教材/文档中搜索相关内容。输入：搜索关键词或问题。",
)


# ----- 记忆工具（构建时注入 user_id）-----

def _make_update_memory_tool(user_id: int):
    def _update(key: str, value: str) -> str:
        UserMemoryManager().set(user_id, key, value)
        return f"已保存记忆: {key} = {value}"

    return StructuredTool.from_function(
        name="update_memory",
        func=_update,
        description="记录用户的偏好、兴趣领域、学习进度等信息。"
                    "参数 key 是分类名称（如 '偏好', '兴趣领域', '学习进度'），"
                    "value 是具体描述。",
    )


def _make_read_memory_tool(user_id: int):
    def _read() -> str:
        mem = UserMemoryManager().format_memory(user_id)
        return mem if mem else "暂无用户记忆"

    return StructuredTool.from_function(
        name="read_memory",
        func=_read,
        description="查看已保存的用户偏好和特征信息。在需要了解用户背景时调用。",
    )


# ----- 复习卡片工具 -----

def _make_create_review_cards_tool(user_id: int):
    import json
    import re

    def _create_cards(topic: str, content: str) -> str:
        from src.config import Config
        from src.knowledge_cache.database import ReviewCardDatabase
        from openai import OpenAI

        client = OpenAI(api_key=Config.DEEPSEEK_API_KEY, base_url=Config.DEEPSEEK_API_BASE)
        try:
            resp = client.chat.completions.create(
                model=Config.DEEPSEEK_MODEL,
                messages=[{
                    "role": "system",
                    "content": f"基于以下学习内容，生成{Config.REVIEW_CARDS_PER_CONVERSATION}个问答复习卡片。"
                               "每个卡片包含一个问题和对应的答案。"
                               "请以JSON数组格式返回："
                               '[{"question": "...", "answer": "..."}]',
                }, {"role": "user", "content": content[:3000]}],
                temperature=0.3,
                max_tokens=2000,
            )
            raw = resp.choices[0].message.content
            raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
            cards = json.loads(raw)
            db = ReviewCardDatabase()
            count = 0
            for card in cards[:Config.REVIEW_CARDS_PER_CONVERSATION]:
                db.save(user_id, card["question"], card["answer"], topic)
                count += 1
            return f"已生成 {count} 张复习卡片，主题：{topic}"
        except Exception as e:
            return f"生成复习卡片失败: {str(e)}"

    return StructuredTool.from_function(
        name="create_review_cards",
        func=_create_cards,
        description="为刚才的学习内容生成问答复习卡片并保存。"
                    "参数 topic 是主题名称，content 是学习内容文本。",
    )


# ----- 知识图谱工具 -----

def _make_update_knowledge_graph_tool(user_id: int):
    import json
    import re

    def _update_graph(topic: str, content: str) -> str:
        from src.config import Config
        from src.knowledge_cache.database import KnowledgeGraphDatabase
        from openai import OpenAI

        client = OpenAI(api_key=Config.DEEPSEEK_API_KEY, base_url=Config.DEEPSEEK_API_BASE)
        try:
            resp = client.chat.completions.create(
                model=Config.DEEPSEEK_MODEL,
                messages=[{
                    "role": "system",
                    "content": "分析以下学习内容，提取核心知识点及其关系。"
                               "请以JSON格式返回，不要用markdown包裹："
                               '{"concepts": [{"name": "...", "description": "..."}],'
                               '"relations": [{"source": "...", "target": "...", "relation": "..."}]}'
                               "relation 字段说明关系类型，如'包含'、'前置'、'应用'、'关联'等。",
                }, {"role": "user", "content": content[:3000]}],
                temperature=0.3,
                max_tokens=2000,
            )
            raw = resp.choices[0].message.content
            raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
            data = json.loads(raw)

            db = KnowledgeGraphDatabase()
            concepts = data.get("concepts", [])
            relations = data.get("relations", [])
            for c in concepts:
                db.upsert_node(user_id, c["name"][:100], c.get("description", "")[:200])
            for r in relations:
                db.upsert_edge(user_id, r["source"][:100], r["target"][:100], r.get("relation", "")[:50])
            return f"已更新知识图谱：新增 {len(concepts)} 个知识点、{len(relations)} 条关系"
        except Exception as e:
            return f"更新知识图谱失败: {str(e)}"

    return StructuredTool.from_function(
        name="update_knowledge_graph",
        func=_update_graph,
        description="从学习内容中提取核心概念及其关系，更新知识图谱。"
                    "参数 topic 是主题名称，content 是学习内容文本。",
    )
