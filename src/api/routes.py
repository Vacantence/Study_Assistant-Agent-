from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import create_token, get_current_user
from src.knowledge_cache.database import (
    UserDatabase,
    ConversationDatabase,
    MessageDatabase,
    ReviewCardDatabase,
    KnowledgeGraphDatabase,
    DocumentDatabase,
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


@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: int, user=Depends(get_current_user)):
    return MessageDatabase().list_by_conversation(conv_id)


@router.post("/chat")
def chat(query: str, conv_id: int | None = None, user=Depends(get_current_user)):
    conv_db = ConversationDatabase()
    msg_db = MessageDatabase()

    if conv_id is None:
        conv_id = conv_db.create(user["id"])

    msg_db.add(conv_id, "user", query)

    # Lazy import to avoid Python 3.14 + pydantic v1 crash on startup
    from src.agent_setup import build_agent
    from langchain_core.messages import AIMessageChunk

    agent = build_agent(user["id"])

    # Build history from DB in (role, content) format
    db_msgs = msg_db.list_by_conversation(conv_id)
    history = [(m["role"], m["content"]) for m in db_msgs if m["role"] in ("user", "assistant")]

    full = ""
    for chunk, _ in agent.stream({"messages": history}, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            full += chunk.content

    filepath = None
    msg_db.add(conv_id, "assistant", full, filepath)

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


# ─── 知识图谱 ────────────────────────────────────────────

@router.get("/graph")
def get_graph(user=Depends(get_current_user)):
    return KnowledgeGraphDatabase().get_graph(user["id"])


# ─── 文档 ────────────────────────────────────────────────

@router.get("/documents")
def list_documents(user=Depends(get_current_user)):
    return DocumentDatabase().list_by_user(user["id"])


# ─── 搜索 ────────────────────────────────────────────────

@router.post("/search")
def search(query: str):
    return search_web.invoke({"query": query})
