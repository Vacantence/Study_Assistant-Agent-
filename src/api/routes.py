from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from src.api.auth import create_token, get_current_user
from src.knowledge_cache.database import (
    UserDatabase,
    ConversationDatabase,
    MessageDatabase,
    ReviewCardDatabase,
    KnowledgeGraphDatabase,
    DocumentDatabase,
    CacheDatabase,
    UserMemoryManager,
    LLMProviderDatabase,
)
from src.tools.search import search_web

router = APIRouter(prefix="/api")


# ─── 认证 ────────────────────────────────────────────────


@router.post("/auth/register")
def register(name: str, password: str):
    user = UserDatabase().register(name, password)
    if not user:
        raise HTTPException(status_code=409, detail="用户名已存在")
    token = create_token(user["id"], user["name"])
    return {"user": user, "token": token}


@router.post("/auth/login")
def login(name: str, password: str):
    user = UserDatabase().authenticate(name, password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user["id"], user["name"])
    return {"user": user, "token": token}


# ─── 对话 ────────────────────────────────────────────────


@router.get("/conversations")
def list_conversations(user=Depends(get_current_user)):
    return ConversationDatabase().list_by_user(user["id"])


@router.post("/conversations")
def create_conversation(user=Depends(get_current_user)):
    conv_id = ConversationDatabase().create(user["id"])
    return {"id": conv_id}


@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: int, user=Depends(get_current_user)):
    return MessageDatabase().list_by_conversation(conv_id)


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int, user=Depends(get_current_user)):
    ConversationDatabase().delete(conv_id)
    return {"status": "ok"}


# ─── SSE 流式聊天 ───────────────────────────────────────


@router.get("/chat/stream")
def chat_stream(query: str, conv_id: int | None = None, user=Depends(get_current_user)):
    conv_db = ConversationDatabase()
    msg_db = MessageDatabase()

    if conv_id is None:
        conv_id = conv_db.create(user["id"])

    msg_db.add(conv_id, "user", query)

    from src.agent_setup import build_agent
    from langchain_core.messages import AIMessageChunk

    agent = build_agent(user["id"])

    db_msgs = msg_db.list_by_conversation(conv_id)
    history = [(m["role"], m["content"]) for m in db_msgs if m["role"] in ("user", "assistant")]

    def event_stream():
        full = ""
        for chunk, _ in agent.stream({"messages": history}, stream_mode="messages"):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                full += chunk.content
                yield f"data: {json.dumps({'token': chunk.content})}\n\n"
        yield f"data: {json.dumps({'metadata': {'conversation_id': conv_id}})}\n\n"
        yield "data: [DONE]\n\n"
        msg_db.add(conv_id, "assistant", full, None)

        convs = conv_db.list_by_user(user["id"])
        if len(convs) == 1:
            conv_db.update_title(conv_id, query[:40])

    import json
    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ─── 同步聊天（保留向后兼容）────────────────────────────


@router.post("/chat")
def chat(query: str, conv_id: int | None = None, user=Depends(get_current_user)):
    conv_db = ConversationDatabase()
    msg_db = MessageDatabase()

    if conv_id is None:
        conv_id = conv_db.create(user["id"])

    msg_db.add(conv_id, "user", query)

    from src.agent_setup import build_agent
    from langchain_core.messages import AIMessageChunk

    agent = build_agent(user["id"])

    db_msgs = msg_db.list_by_conversation(conv_id)
    history = [(m["role"], m["content"]) for m in db_msgs if m["role"] in ("user", "assistant")]

    full = ""
    for chunk, _ in agent.stream({"messages": history}, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            full += chunk.content

    msg_db.add(conv_id, "assistant", full, None)

    convs = conv_db.list_by_user(user["id"])
    if len(convs) == 1:
        conv_db.update_title(conv_id, query[:40])

    return {"conversation_id": conv_id, "response": full}


# ─── 导出 ────────────────────────────────────────────────


@router.get("/conversations/{conv_id}/export")
def export_conversation(conv_id: int, user=Depends(get_current_user)):
    from src.tools.export import export_conversation_markdown
    conv = ConversationDatabase().get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    title = conv["title"]
    md = export_conversation_markdown(conv_id, title)
    return {"title": title, "markdown": md}


# ─── 复习卡片 ────────────────────────────────────────────


@router.get("/review/cards")
def get_review_cards(user=Depends(get_current_user)):
    return ReviewCardDatabase().get_due(user["id"])


@router.post("/review/cards/{card_id}/review")
def review_card(card_id: int, quality: int, user=Depends(get_current_user)):
    if quality < 1 or quality > 5:
        raise HTTPException(status_code=422, detail="评分需在 1-5 之间")
    ReviewCardDatabase().update_review(card_id, quality)
    return {"status": "ok", "card_id": card_id, "quality": quality}


@router.delete("/review/cards/{card_id}")
def delete_review_card(card_id: int, user=Depends(get_current_user)):
    ReviewCardDatabase().delete(card_id)
    return {"status": "ok"}


# ─── 知识图谱 ────────────────────────────────────────────


@router.get("/graph")
def get_graph(user=Depends(get_current_user)):
    return KnowledgeGraphDatabase().get_graph(user["id"])


@router.delete("/graph")
def clear_graph(user=Depends(get_current_user)):
    KnowledgeGraphDatabase().clear(user["id"])
    return {"status": "ok"}


# ─── 文档 ────────────────────────────────────────────────


@router.get("/documents")
def list_documents(user=Depends(get_current_user)):
    return DocumentDatabase().list_by_user(user["id"])


@router.post("/documents/upload")
def upload_document(file: UploadFile = File(...), user=Depends(get_current_user)):
    from src.tools.document_loader import parse_document, chunk_text
    from src.knowledge_cache.embeddings import EmbeddingManager

    filename = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"
    raw = file.file.read()

    doc_db = DocumentDatabase()
    doc_id = doc_db.save_document(user["id"], filename, content_type)

    text = parse_document(raw, filename)
    chunks = chunk_text(text)
    emb = EmbeddingManager()

    for i, chunk_text_content in enumerate(chunks):
        vec = emb.embed_text(chunk_text_content)
        import numpy as np
        blob = np.array(vec, dtype=np.float32).tobytes()
        doc_db.save_chunk(doc_id, i, chunk_text_content, blob)

    return {"id": doc_id, "filename": filename, "chunk_count": len(chunks)}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, user=Depends(get_current_user)):
    DocumentDatabase().delete(doc_id)
    return {"status": "ok"}


# ─── 用户记忆 ────────────────────────────────────────────


@router.get("/memory")
def get_memory(user=Depends(get_current_user)):
    mem = UserMemoryManager().get_all(user["id"])
    return [{"key": m["key"], "value": m["value"]} for m in mem]


# ─── 知识库缓存 ──────────────────────────────────────────


@router.get("/cache")
def list_cache(user=Depends(get_current_user)):
    return CacheDatabase().get_all()


@router.delete("/cache/{cache_id}")
def delete_cache(cache_id: int, user=Depends(get_current_user)):
    CacheDatabase().delete(cache_id)
    return {"status": "ok"}


@router.delete("/cache")
def clear_cache(user=Depends(get_current_user)):
    CacheDatabase().clear_all()
    return {"status": "ok"}


# ─── 统计 ────────────────────────────────────────────────


@router.get("/stats")
def get_stats(user=Depends(get_current_user)):
    review = ReviewCardDatabase().get_stats(user["id"])
    graph = KnowledgeGraphDatabase().get_stats(user["id"])
    return {
        "review_due": review["due"],
        "graph_nodes": graph["nodes"],
    }


# ─── 搜索 ────────────────────────────────────────────────


@router.post("/search")
def search(query: str):
    return search_web.invoke({"query": query})


# ─── LLM 提供商配置 ────────────────────────────────────────


@router.get("/llm/providers")
def list_providers(user=Depends(get_current_user)):
    return LLMProviderDatabase().list_by_user(user["id"])


@router.get("/llm/providers/active")
def get_active_provider(user=Depends(get_current_user)):
    provider = LLMProviderDatabase().get_active(user["id"])
    if not provider:
        from src.config import Config
        return {
            "id": None,
            "name": "默认 (DeepSeek)",
            "api_base": Config.DEEPSEEK_API_BASE,
            "model": Config.DEEPSEEK_MODEL,
            "is_active": True,
        }
    return provider


@router.post("/llm/providers")
def add_provider(name: str, api_base: str, api_key: str, model: str, user=Depends(get_current_user)):
    if not name or not api_base or not api_key or not model:
        raise HTTPException(status_code=422, detail="所有字段均为必填")
    provider_id = LLMProviderDatabase().add(user["id"], name, api_base, api_key, model)
    return {"id": provider_id}


@router.put("/llm/providers/{provider_id}")
def update_provider(provider_id: int, name: str, api_base: str, api_key: str, model: str, user=Depends(get_current_user)):
    provider = LLMProviderDatabase().get_by_id(provider_id)
    if not provider or provider["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="提供商不存在")
    LLMProviderDatabase().update(provider_id, name, api_base, api_key, model)
    return {"status": "ok"}


@router.post("/llm/providers/{provider_id}/activate")
def activate_provider(provider_id: int, user=Depends(get_current_user)):
    provider = LLMProviderDatabase().get_by_id(provider_id)
    if not provider or provider["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="提供商不存在")
    LLMProviderDatabase().set_active(user["id"], provider_id)
    return {"status": "ok"}


@router.delete("/llm/providers/{provider_id}")
def delete_provider(provider_id: int, user=Depends(get_current_user)):
    provider = LLMProviderDatabase().get_by_id(provider_id)
    if not provider or provider["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="提供商不存在")
    LLMProviderDatabase().delete(provider_id, user["id"])
    return {"status": "ok"}
