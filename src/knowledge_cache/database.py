import hashlib
import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import Optional

from src.config import Config


def _get_connection():
    conn = sqlite3.connect(Config.CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                summary TEXT NOT NULL,
                sources TEXT NOT NULL,
                embedding BLOB,
                quality_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kc_query ON knowledge_cache(query)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                filepath TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, key)
            )
        """)

        # 文档库
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_user ON documents(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc ON document_chunks(document_id)
        """)

        # 复习卡片
        conn.execute("""
            CREATE TABLE IF NOT EXISTS review_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                topic TEXT NOT NULL,
                easiness REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                next_review TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_user ON review_cards(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_next ON review_cards(next_review)
        """)

        # 知识图谱
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, source, target, relation)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kn_user ON knowledge_nodes(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ke_user ON knowledge_edges(user_id)
        """)

        # 迁移：老表可能缺少列
        try:
            conn.execute("ALTER TABLE messages ADD COLUMN filepath TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT DEFAULT ''")
        except Exception:
            pass


# ----- 知识缓存 -----

class CacheDatabase:
    def cleanup(self):
        """缓存淘汰：移除低质量 + 超限条目"""
        from src.config import Config
        with _get_connection() as conn:
            # 1. 移除低质量且无访问的记录
            conn.execute(
                "DELETE FROM knowledge_cache WHERE quality_score < ? AND access_count = 0",
                (Config.CACHE_MIN_QUALITY,)
            )
            # 2. 超出上限则删除最旧的
            count = conn.execute("SELECT COUNT(*) FROM knowledge_cache").fetchone()[0]
            if count > Config.CACHE_MAX_ENTRIES:
                conn.execute(
                    """DELETE FROM knowledge_cache WHERE id IN (
                        SELECT id FROM knowledge_cache
                        ORDER BY quality_score DESC, access_count DESC
                        LIMIT -1 OFFSET ?
                    )""",
                    (Config.CACHE_MAX_ENTRIES,)
                )

    def save(self, query: str, summary: str, sources: list[str],
             embedding: bytes = None, quality_score: float = 0.0) -> int:
        with _get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO knowledge_cache
                   (query, summary, sources, embedding, quality_score, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (query, summary, json.dumps(sources),
                 embedding, quality_score, datetime.now().isoformat())
            )
            return cur.lastrowid

    def get_all_with_embeddings(self) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM knowledge_cache ORDER BY quality_score DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all(self) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                """SELECT id, query, created_at, quality_score, access_count
                   FROM knowledge_cache ORDER BY created_at DESC"""
            ).fetchall()
            return [dict(r) for r in rows]

    def increment_access(self, cache_id: int):
        with _get_connection() as conn:
            conn.execute(
                "UPDATE knowledge_cache SET access_count = access_count + 1 WHERE id = ?",
                (cache_id,)
            )

    def delete(self, cache_id: int):
        with _get_connection() as conn:
            conn.execute("DELETE FROM knowledge_cache WHERE id = ?", (cache_id,))

    def clear_all(self):
        with _get_connection() as conn:
            conn.execute("DELETE FROM knowledge_cache")


# ----- 用户 / 会话 / 消息 -----

class UserDatabase:
    def get_or_create(self, name: str) -> dict:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return dict(row)
            cur = conn.execute(
                "INSERT INTO users (name, created_at) VALUES (?, ?)",
                (name, datetime.now().isoformat())
            )
            return {"id": cur.lastrowid, "name": name}

    def register(self, name: str, password: str) -> dict | None:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return None
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            cur = conn.execute(
                "INSERT INTO users (name, password_hash, created_at) VALUES (?, ?, ?)",
                (name, pw_hash, datetime.now().isoformat()),
            )
            return {"id": cur.lastrowid, "name": name}

    def authenticate(self, name: str, password: str) -> dict | None:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, password_hash FROM users WHERE name = ?", (name,)
            ).fetchone()
            if not row:
                return None
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            if row["password_hash"] and row["password_hash"] != pw_hash:
                return None
            return {"id": row["id"], "name": row["name"]}

    def get_by_id(self, user_id: int) -> dict | None:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT id, name FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all(self) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]


class ConversationDatabase:
    def create(self, user_id: int, title: str = "新对话") -> int:
        now = datetime.now().isoformat()
        with _get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO conversations (user_id, title, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (user_id, title, now, now)
            )
            return cur.lastrowid

    def list_by_user(self, user_id: int) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                """SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as msg_count
                   FROM conversations c WHERE c.user_id = ?
                   ORDER BY c.updated_at DESC""",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_by_id(self, conv_id: int) -> dict | None:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conv_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_title(self, conv_id: int, title: str):
        with _get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, datetime.now().isoformat(), conv_id)
            )

    def delete(self, conv_id: int):
        with _get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))


class MessageDatabase:
    def add(self, conversation_id: int, role: str, content: str,
            filepath: str = None) -> int:
        with _get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO messages (conversation_id, role, content, filepath, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (conversation_id, role, content, filepath, datetime.now().isoformat())
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), conversation_id)
            )
            return cur.lastrowid

    def list_by_conversation(self, conversation_id: int) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_last_message(self, conversation_id: int) -> Optional[dict]:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 1",
                (conversation_id,)
            ).fetchone()
            return dict(row) if row else None


class UserMemoryManager:
    def get_all(self, user_id: int) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT key, value FROM user_memory WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def set(self, user_id: int, key: str, value: str):
        with _get_connection() as conn:
            conn.execute(
                """INSERT INTO user_memory (user_id, key, value, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, key) DO UPDATE SET value = ?, updated_at = ?""",
                (user_id, key, value, datetime.now().isoformat(),
                 value, datetime.now().isoformat())
            )

    def format_memory(self, user_id: int) -> str:
        """返回格式化的记忆文本，用于注入 system prompt"""
        items = self.get_all(user_id)
        if not items:
            return ""
        parts = [f"- {m['key']}: {m['value']}" for m in items]
        return "用户偏好与特征：\n" + "\n".join(parts)


# ----- 文档库 -----

class DocumentDatabase:
    def save_document(self, user_id: int, filename: str, content_type: str) -> int:
        with _get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO documents (user_id, filename, content_type, chunk_count, created_at) VALUES (?, ?, ?, 0, ?)",
                (user_id, filename, content_type, datetime.now().isoformat()),
            )
            return cur.lastrowid

    def save_chunk(self, document_id: int, chunk_index: int, content: str, embedding: bytes = None):
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO document_chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                (document_id, chunk_index, content, embedding),
            )
            conn.execute(
                "UPDATE documents SET chunk_count = chunk_count + 1 WHERE id = ?",
                (document_id,),
            )

    def list_by_user(self, user_id: int) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete(self, doc_id: int):
        with _get_connection() as conn:
            conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    def get_all_chunks_with_embeddings(self) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT c.*, d.filename FROM document_chunks c JOIN documents d ON c.document_id = d.id WHERE c.embedding IS NOT NULL"
            ).fetchall()
            return [dict(r) for r in rows]


# ----- 复习卡片 (SM-2) -----

class ReviewCardDatabase:
    def save(self, user_id: int, question: str, answer: str, topic: str) -> int:
        now = datetime.now().isoformat()
        with _get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO review_cards
                   (user_id, question, answer, topic, next_review, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, question, answer, topic, date.today().isoformat(), now, now),
            )
            return cur.lastrowid

    def get_due(self, user_id: int) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM review_cards WHERE user_id = ? AND next_review <= ? ORDER BY next_review",
                (user_id, date.today().isoformat()),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self, user_id: int) -> dict:
        with _get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM review_cards WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            due = conn.execute(
                "SELECT COUNT(*) FROM review_cards WHERE user_id = ? AND next_review <= ?",
                (user_id, date.today().isoformat()),
            ).fetchone()[0]
            return {"total": total, "due": due}

    def update_review(self, card_id: int, quality: int):
        """SM-2 算法更新卡片复习计划"""
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM review_cards WHERE id = ?", (card_id,)
            ).fetchone()
            if not row:
                return

            easiness = row["easiness"]
            interval = row["interval_days"]
            reps = row["repetitions"]

            if quality >= 3:
                if reps == 0:
                    interval = 1
                elif reps == 1:
                    interval = 6
                else:
                    interval = round(interval * easiness)
                reps += 1
            else:
                reps = 0
                interval = 1

            easiness += 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            if easiness < 1.3:
                easiness = 1.3

            next_review = (date.today() + timedelta(days=interval)).isoformat()

            conn.execute(
                """UPDATE review_cards SET easiness=?, interval_days=?, repetitions=?,
                   next_review=?, updated_at=? WHERE id=?""",
                (easiness, interval, reps, next_review, datetime.now().isoformat(), card_id),
            )

    def list_recent(self, user_id: int, limit: int = 10) -> list[dict]:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM review_cards WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete(self, card_id: int):
        with _get_connection() as conn:
            conn.execute("DELETE FROM review_cards WHERE id = ?", (card_id,))


# ----- 知识图谱 -----

class KnowledgeGraphDatabase:
    def upsert_node(self, user_id: int, name: str, description: str = ""):
        now = datetime.now().isoformat()
        with _get_connection() as conn:
            conn.execute(
                """INSERT INTO knowledge_nodes (user_id, name, description, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(user_id, name) DO UPDATE SET
                       description = CASE WHEN length(?) > length(description) THEN ? ELSE description END,
                       updated_at = ?""",
                (user_id, name, description, now, now, description, description, now),
            )

    def upsert_edge(self, user_id: int, source: str, target: str, relation: str = ""):
        now = datetime.now().isoformat()
        with _get_connection() as conn:
            conn.execute(
                """INSERT INTO knowledge_edges (user_id, source, target, relation, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(user_id, source, target, relation) DO NOTHING""",
                (user_id, source, target, relation, now),
            )

    def get_graph(self, user_id: int) -> dict:
        with _get_connection() as conn:
            nodes = conn.execute(
                "SELECT name, description FROM knowledge_nodes WHERE user_id = ? ORDER BY name",
                (user_id,),
            ).fetchall()
            edges = conn.execute(
                "SELECT source, target, relation FROM knowledge_edges WHERE user_id = ? ORDER BY source",
                (user_id,),
            ).fetchall()
            return {
                "nodes": [dict(r) for r in nodes],
                "edges": [dict(r) for r in edges],
            }

    def get_stats(self, user_id: int) -> dict:
        with _get_connection() as conn:
            nodes = conn.execute(
                "SELECT COUNT(*) FROM knowledge_nodes WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            edges = conn.execute(
                "SELECT COUNT(*) FROM knowledge_edges WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            return {"nodes": nodes, "edges": edges}

    def clear(self, user_id: int):
        with _get_connection() as conn:
            conn.execute("DELETE FROM knowledge_edges WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM knowledge_nodes WHERE user_id = ?", (user_id,))


# 初始化
init_db()
