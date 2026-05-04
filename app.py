import os
import re

import streamlit as st

from src.config import Config
from src.knowledge_cache.database import (
    CacheDatabase,
    UserDatabase,
    ConversationDatabase,
    MessageDatabase,
    DocumentDatabase,
    ReviewCardDatabase,
    KnowledgeGraphDatabase,
)

st.set_page_config(page_title="AI 学习助手", page_icon=":material/school:", layout="wide")

st.markdown("""<style>
    .stSpinner > div { border-color: #10b981 #10b981 transparent transparent !important; }
    section[data-testid="stAppViewBlockContainer"] { overflow: visible !important; }
    div[data-testid="stVerticalBlockBorderBox"]:has(> div.st-key-nav-container) {
        position: sticky !important; top: 0 !important; z-index: 999 !important;
        background-color: #FFFFFF !important; padding-top: 0.5rem !important;
        border-bottom: 1px solid #e0e0e0 !important;
    }
</style>""", unsafe_allow_html=True)

NAV_ITEMS = {  # label → icon
    "chat": ("💬", "对话"),
    "docs": ("📄", "资料库"),
    "review": ("🔄", "复习"),
    "graph": ("🕸", "知识图谱"),
}


# ----- 会话初始化（进度条） -----
def init_state():
    if "ready" in st.session_state:
        return

    placeholder = st.empty()
    with placeholder.container():
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown("<h2 style='text-align: center;'>AI 学习助手</h2>", unsafe_allow_html=True)
            bar = st.progress(0, text="正在加载 AI 引擎...")
            from src.agent_setup import build_agent
            agent = build_agent()
            bar.progress(0.45, text="正在连接知识库...")

            from src.knowledge_cache.embeddings import EmbeddingManager
            EmbeddingManager()
            bar.progress(0.8, text="正在清理旧缓存...")

            CacheDatabase().cleanup()
            bar.progress(1.0, text="准备就绪!")

    st.session_state.agent = agent
    st.session_state.agent_user_id = None
    st.session_state.messages = []
    st.session_state.current_user = None
    st.session_state.current_conv_id = None
    st.session_state.cache_mode = "auto"
    st.session_state.nav = "chat"
    st.session_state.review_idx = 0
    st.session_state.show_answer = False
    st.session_state.ready = True

    placeholder.empty()
    st.rerun()


# ----- 记忆管理 -----
def _ensure_agent_for_user(user_id: int):
    if st.session_state.get("agent_user_id") != user_id:
        from src.agent_setup import build_agent
        st.session_state.agent = build_agent(user_id)
        st.session_state.agent_user_id = user_id


# ----- 流式输出 -----
def _fix_formulas(text: str) -> str:
    text = re.sub(r'\\\(', '$', text)
    text = re.sub(r'\\\)', '$', text)
    text = re.sub(r'\\\[', '$$', text)
    text = re.sub(r'\\\]', '$$', text)
    return text


def _stream_agent(agent, history):
    from langchain_core.messages import AIMessageChunk
    for chunk, _ in agent.stream(
        {"messages": history},
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content


# ----- 历史窗口管理 -----
def _prepare_history() -> list[tuple[str, str]]:
    msgs = st.session_state.messages
    pairs = [(m["role"], m["content"]) for m in msgs]
    max_pairs = Config.MAX_HISTORY_PAIRS * 2
    if len(pairs) <= max_pairs:
        return pairs

    recent = pairs[-max_pairs:]
    early = pairs[:-max_pairs]
    early_text = "\n".join(
        f"{'用户' if r == 'user' else '助手'}: {c[:200]}"
        for r, c in early
    )
    summary = compress_text(early_text)
    return [("system", f"以下为早期对话摘要：\n{summary}")] + recent


# ----- 工具函数 -----
def _get_openai_client():
    if "openai_client" not in st.session_state:
        from openai import OpenAI
        st.session_state.openai_client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_API_BASE,
        )
    return st.session_state.openai_client


def compress_text(text: str) -> str:
    if len(text) < 500:
        return text
    try:
        resp = _get_openai_client().chat.completions.create(
            model=Config.DEEPSEEK_MODEL,
            messages=[{
                "role": "system",
                "content": "压缩以下内容为2-3段精华摘要，保留核心知识点。"
            }, {"role": "user", "content": text[:3000]}],
            temperature=0.3,
            max_tokens=500,
        )
        return resp.choices[0].message.content or text[:1000]
    except Exception:
        return text[:1000]


def save_to_cache(query: str, content: str):
    import numpy as np
    from src.knowledge_cache.embeddings import EmbeddingManager
    emb = EmbeddingManager()
    cache_db = CacheDatabase()

    records = cache_db.get_all_with_embeddings()
    if records:
        _, score = emb.find_best_match(query, records)
        if score >= Config.CACHE_SIMILARITY_THRESHOLD:
            return

    compressed = compress_text(content)
    vec = emb.embed_text(query + " " + compressed)
    cache_db.save(query, compressed, [],
                  np.array(vec, dtype=np.float32).tobytes(),
                  min(len(compressed) / 300, 1.0))


def generate_learning_doc(content: str, topic: str) -> str | None:
    try:
        from src.tools.document import generate_doc
        return generate_doc.invoke({"content": content, "topic": topic, "fmt": "md"})
    except Exception:
        return None


def process_uploaded_document(uploaded, user_id: int, doc_db: DocumentDatabase):
    import numpy as np
    from src.tools.document_loader import parse_document, chunk_text
    from src.knowledge_cache.embeddings import EmbeddingManager

    ext_map = {"pdf": "application/pdf", "docx": "application/docx", "txt": "text/plain"}
    doc_id = doc_db.save_document(user_id, uploaded.name, ext_map.get(uploaded.type, "unknown"))

    text = parse_document(uploaded.read(), uploaded.name)
    chunks = chunk_text(text)

    emb = EmbeddingManager()
    for idx, chunk in enumerate(chunks):
        vec = emb.embed_text(chunk)
        doc_db.save_chunk(doc_id, idx, chunk, np.array(vec, dtype=np.float32).tobytes())

# ----- 对话管理 -----

def _load_messages(conv_id: int):
    st.session_state.current_conv_id = conv_id
    st.session_state.messages = []
    for msg in MessageDatabase().list_by_conversation(conv_id):
        entry = {"role": msg["role"], "content": msg["content"]}
        if msg.get("filepath"):
            entry["filepath"] = msg["filepath"]
        st.session_state.messages.append(entry)


def _new_conversation(user_id: int):
    conv_id = ConversationDatabase().create(user_id)
    _load_messages(conv_id)


# ----- 导航栏 -----

def render_nav_bar():
    current = st.session_state.get("nav", "chat")
    cols = st.columns(len(NAV_ITEMS))
    for col, (key, (icon, label)) in zip(cols, NAV_ITEMS.items()):
        with col:
            active = key == current
            btn_label = f"{icon} {label}"
            if st.button(btn_label, key=f"nav_{key}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.nav = key
                st.rerun()


# ----- 侧边栏 -----

def render_sidebar() -> str:
    conv_db = ConversationDatabase()
    cache_db = CacheDatabase()

    cu = st.session_state.current_user
    st.sidebar.caption(f":material/person: **{cu['name']}**")

    if st.sidebar.button(":material/logout: 切换用户", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.messages = []
        st.session_state.current_conv_id = None
        st.session_state.agent_user_id = None
        st.rerun()

    # ---- 用户记忆 ----
    from src.knowledge_cache.database import UserMemoryManager
    mems = UserMemoryManager().get_all(cu["id"])
    with st.sidebar.expander(f":material/psychology: 记忆 ({len(mems)})", expanded=False):
        if mems:
            for m in mems:
                st.caption(f"**{m['key']}**: {m['value'][:60]}")
        else:
            st.caption("暂无记忆 — 提问后 agent 会自动记录你的偏好")

    # ---- 对话区域 ----
    st.sidebar.divider()
    st.sidebar.header(":material/chat: 对话")

    if st.sidebar.button(":material/add_circle:  新对话", use_container_width=True):
        _new_conversation(cu["id"])
        st.rerun()

    for conv in conv_db.list_by_user(cu["id"]):
        active = conv["id"] == st.session_state.current_conv_id
        label = conv["title"][:28]
        msg_count = conv["msg_count"]
        count_str = f"({msg_count})" if msg_count else ""

        col1, col2 = st.sidebar.columns([5, 1])
        with col1:
            btn_text = f":material/forum: **{label}** {count_str}" if active else f"\U0000FE58 {label} {count_str}"
            if st.button(btn_text, key=f"c_{conv['id']}", use_container_width=True):
                _load_messages(conv["id"])
                st.rerun()
        with col2:
            if st.button(":material/delete:", key=f"d_{conv['id']}"):
                ConversationDatabase().delete(conv["id"])
                if active:
                    st.session_state.current_conv_id = None
                    st.session_state.messages = []
                st.rerun()

    if st.session_state.current_conv_id:
        if st.sidebar.button(":material/download: 导出对话", use_container_width=True):
            from src.tools.export import export_conversation_markdown, save_export_file
            conv = conv_db.get_by_id(st.session_state.current_conv_id)
            title = conv["title"] if conv else "对话记录"
            md = export_conversation_markdown(st.session_state.current_conv_id, title)
            fp = save_export_file(md, title)
            with open(fp, "rb") as f:
                st.sidebar.download_button(
                    ":material/save_alt: 下载 Markdown",
                    f, file_name=os.path.basename(fp), mime="text/markdown",
                    use_container_width=True,
                )

    # ---- 知识库区域 ----
    st.sidebar.divider()
    st.sidebar.header(":material/database: 知识库")

    mode_map = {"自动缓存": "auto", "仅查询不存储": "query_only", "清空知识库": "clear"}
    sel_mode = st.sidebar.radio("模式", list(mode_map.keys()),
                                label_visibility="collapsed", key="cache_mode_radio")
    cm = mode_map[sel_mode]

    if cm == "clear":
        if st.sidebar.button("确认清空"):
            cache_db.clear_all()
            st.rerun()
    elif cm != st.session_state.cache_mode:
        st.session_state.cache_mode = cm

    for r in cache_db.get_all()[:5]:
        st.sidebar.caption(f"{r['query'][:25]}  (评分 {r['quality_score']:.1f})")

    # ---- 小部件：复习 & 图谱快捷统计 ----
    st.sidebar.divider()
    rstats = ReviewCardDatabase().get_stats(cu["id"])
    gstats = KnowledgeGraphDatabase().get_stats(cu["id"])
    st.sidebar.caption(
        f":material/auto_stories: **{rstats['due']}** 张待复习  "
        f"| :material/hub: **{gstats['nodes']}** 知识点"
    )

    st.sidebar.divider()
    st.sidebar.caption(f"模型: {Config.DEEPSEEK_MODEL}")
    return cm


# ----- 各个页面 -----

def render_chat_page(cache_mode: str):
    cu = st.session_state.current_user

    # 显示消息历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(_fix_formulas(msg["content"]))
            fp = msg.get("filepath")
            if fp and os.path.exists(fp):
                with open(fp, "rb") as f:
                    st.download_button(
                        ":material/download: 下载文档", f,
                        file_name=os.path.basename(fp), mime="text/markdown",
                    )

    # 输入框
    if prompt := st.chat_input("输入你想学习的问题..."):
        conv_id = st.session_state.current_conv_id
        if conv_id is None:
            conv_id = ConversationDatabase().create(cu["id"])
            st.session_state.current_conv_id = conv_id

        MessageDatabase().add(conv_id, "user", prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            from src.agent_setup import build_agent
            agent = build_agent(cu["id"])
            st.session_state.agent = agent
            history = _prepare_history()

            status = st.status("正在搜索研究...", state="running")
            msg_area = st.empty()

            full = ""
            for chunk in _stream_agent(agent, history):
                if not full:
                    status.update(label="正在生成回答...", state="running")
                full += chunk
                msg_area.markdown(_fix_formulas(full) + "▌")

            msg_area.markdown(_fix_formulas(full))
            status.update(label="回答完成", state="complete")
            response = full

            with st.spinner(":material/save:  保存知识库..."):
                if cache_mode != "query_only":
                    save_to_cache(prompt, response)

            with st.spinner(":material/description:  生成文档..."):
                filepath = generate_learning_doc(response, prompt[:30])
                if filepath:
                    with open(filepath, "rb") as f:
                        st.download_button(
                            ":material/download: 下载学习文档", f,
                            file_name=os.path.basename(filepath), mime="text/markdown",
                        )

            MessageDatabase().add(conv_id, "assistant", response, filepath)
            entry = {"role": "assistant", "content": response}
            if filepath:
                entry["filepath"] = filepath
            st.session_state.messages.append(entry)

        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if len(user_msgs) == 1:
            ConversationDatabase().update_title(conv_id, prompt[:40])


def render_docs_page():
    cu = st.session_state.current_user
    st.subheader(":material/description: 资料库")

    doc_db = DocumentDatabase()
    uploaded = st.file_uploader(
        "上传教材/文档（PDF / Word / TXT）",
        type=["pdf", "docx", "txt"],
        key="docs_uploader",
    )

    if uploaded:
        existing = [d["filename"] for d in doc_db.list_by_user(cu["id"])]
        if uploaded.name not in existing:
            with st.spinner("正在解析并建立索引..."):
                process_uploaded_document(uploaded, cu["id"], doc_db)
            st.rerun()
        else:
            st.info(f"《{uploaded.name}》已存在")

    docs = doc_db.list_by_user(cu["id"])
    if docs:
        st.markdown(f"已上传 **{len(docs)}** 份文档：")
        for doc in docs:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.caption(f":material/article: {doc['filename']} ({doc['chunk_count']} 段)")
            with col2:
                if st.button(":material/delete:", key=f"dd_{doc['id']}"):
                    doc_db.delete(doc["id"])
                    st.rerun()
    else:
        st.info("尚未上传任何文档")


def render_review_ui():
    cu = st.session_state.current_user
    st.subheader(":material/auto_stories: 复习")

    db = ReviewCardDatabase()
    cards = db.get_due(cu["id"])

    if not cards:
        st.success("暂无待复习的卡片！继续学习来生成新卡片。")
        return

    idx = st.session_state.get("review_idx", 0)
    if idx >= len(cards):
        st.session_state.review_idx = 0
        idx = 0

    card = cards[idx]

    st.progress((idx + 1) / len(cards))
    st.caption(f"第 {idx + 1} / {len(cards)} 张   |   主题: {card['topic']}")

    with st.container(border=True):
        st.markdown("**问题：**")
        st.markdown(card["question"])

    if st.session_state.get("show_answer"):
        with st.container(border=True):
            st.markdown("**答案：**")
            st.markdown(card["answer"])

        st.caption("你掌握得怎么样？")
        cols = st.columns(5)
        labels = ["完全忘了", "很模糊", "有点印象", "基本记住", "非常熟练"]
        for i, (col, label) in enumerate(zip(cols, labels)):
            quality = i + 1
            with col:
                if st.button(f"{quality}分\n{label}", key=f"q_{idx}_{quality}", use_container_width=True):
                    db.update_review(card["id"], quality)
                    st.session_state.review_idx = idx + 1
                    st.session_state.show_answer = False
                    st.rerun()

        if st.button(":material/delete: 删除此卡片", key=f"del_{idx}"):
            db.delete(card["id"])
            st.session_state.review_idx = idx
            st.session_state.show_answer = False
            st.rerun()
    else:
        if st.button(":material/visibility: 显示答案", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()


def render_knowledge_graph_ui():
    cu = st.session_state.current_user
    st.subheader(":material/hub: 知识图谱")

    db = KnowledgeGraphDatabase()
    graph = db.get_graph(cu["id"])

    if not graph["nodes"]:
        st.info("暂无知识点，继续学习来构建你的知识图谱！")
        return

    mermaid_lines = ["flowchart LR"]
    for edge in graph["edges"]:
        src = re.sub(r'[()"\[\]]', "", edge["source"])
        tgt = re.sub(r'[()"\[\]]', "", edge["target"])
        rel = edge.get("relation", "")
        mermaid_lines.append(f'    {src} -->|{rel}| {tgt}' if rel else f'    {src} --> {tgt}')

    st.markdown(f"```mermaid\n{chr(10).join(mermaid_lines)}\n```")

    with st.expander(f":material/list: 全部知识点 ({len(graph['nodes'])} 个)"):
        for node in graph["nodes"]:
            desc = node["description"] if node["description"] else "无描述"
            st.markdown(f"- **{node['name']}**: {desc}")

    if st.button(":material/delete_sweep: 清空图谱"):
        db.clear(cu["id"])
        st.rerun()


# ----- 登录 / 注册页面 -----

def render_login_page():
    st.markdown("<h1 style='text-align: center;'>AI 学习助手</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>登录后开始你的学习之旅</p>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        tab1, tab2 = st.tabs(["登录", "注册"])

        with tab1:
            with st.form("login_form", clear_on_submit=True):
                l_name = st.text_input("用户名", placeholder="请输入用户名")
                l_pw = st.text_input("密码", type="password", placeholder="请输入密码")
                l_sub = st.form_submit_button("登录", use_container_width=True)
                if l_sub:
                    if not l_name or not l_pw:
                        st.error("请填写用户名和密码")
                    else:
                        user = UserDatabase().authenticate(l_name, l_pw)
                        if user:
                            from src.knowledge_cache.database import ConversationDatabase
                            _ensure_agent_for_user(user["id"])
                            st.session_state.current_user = user
                            convs = ConversationDatabase().list_by_user(user["id"])
                            if convs:
                                _load_messages(convs[0]["id"])
                            else:
                                _new_conversation(user["id"])
                            st.rerun()
                        else:
                            st.error("用户名或密码错误")

        with tab2:
            with st.form("register_form", clear_on_submit=True):
                r_name = st.text_input("用户名", placeholder="请输入用户名", key="reg_name")
                r_pw = st.text_input("密码", type="password", placeholder="至少 4 位", key="reg_pw")
                r_cfm = st.text_input("确认密码", type="password", placeholder="再次输入密码", key="reg_cfm")
                r_sub = st.form_submit_button("注册", use_container_width=True)
                if r_sub:
                    if not r_name or not r_pw:
                        st.error("请填写用户名和密码")
                    elif len(r_pw) < 4:
                        st.error("密码至少 4 位")
                    elif r_pw != r_cfm:
                        st.error("两次密码不一致")
                    else:
                        user = UserDatabase().register(r_name, r_pw)
                        if user:
                            _ensure_agent_for_user(user["id"])
                            st.session_state.current_user = user
                            _new_conversation(user["id"])
                            st.rerun()
                        else:
                            st.error("用户名已存在")


# ----- 主界面 -----

def main():
    init_state()

    cu = st.session_state.current_user
    if not cu:
        render_login_page()
        return

    st.title(":material/school: AI 学习助手")
    cache_mode = render_sidebar()

    with st.container(key="nav-container"):
        render_nav_bar()

    nav = st.session_state.get("nav", "chat")
    if nav == "docs":
        render_docs_page()
    elif nav == "review":
        render_review_ui()
    elif nav == "graph":
        render_knowledge_graph_ui()
    else:
        render_chat_page(cache_mode)


if __name__ == "__main__":
    main()
