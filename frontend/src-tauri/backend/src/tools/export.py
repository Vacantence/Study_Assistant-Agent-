"""对话历史导出功能"""

import os
from datetime import datetime

from src.config import Config
from src.knowledge_cache.database import MessageDatabase


def export_conversation_markdown(conv_id: int, title: str = "对话记录") -> str:
    """导出对话为 Markdown 字符串"""
    msgs = MessageDatabase().list_by_conversation(conv_id)
    lines = [f"# {title}\n", f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    ROLE_LABEL = {"user": "**你**", "assistant": "**AI 助手**"}

    for msg in msgs:
        role = msg["role"]
        if role not in ROLE_LABEL:
            continue
        lines.append(f"\n---\n### {ROLE_LABEL[role]}\n")
        lines.append(msg["content"])

    return "\n".join(lines)


def save_export_file(content: str, title: str) -> str:
    """保存导出文件到 outputs 目录，返回文件路径"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:40]
    filename = f"{date_str}_对话_{safe_title}.md"
    filepath = os.path.join(Config.OUTPUT_DIR, filename)
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath
