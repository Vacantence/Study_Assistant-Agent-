import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-chat"

    # 知识缓存配置
    CACHE_DB_PATH = "knowledge_cache.db"
    CACHE_SIMILARITY_THRESHOLD = 0.85
    CACHE_MODE = "auto"  # auto | manual | query_only

    # 阿里云千问 Embedding
    ALIYUN_EMBEDDING_API_KEY = os.getenv("ALIYUN_EMBEDDING_API_KEY", "sk-e01ad98dc2b24ca3baac099816ce45d2")
    ALIYUN_EMBEDDING_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALIYUN_EMBEDDING_MODEL = "text-embedding-v3"

    # 搜索配置
    SEARCH_TOP_K = 5

    # 文档配置
    OUTPUT_DIR = "outputs"

    # 记忆管理
    MAX_HISTORY_PAIRS = 15  # 保留最近 N 轮问答，旧轮压缩为摘要

    # 缓存淘汰
    CACHE_MAX_ENTRIES = 200      # 知识缓存上限
    CACHE_MIN_QUALITY = 0.3      # 低于此分且无访问的条目会被清理

    # 复习卡片 (SM-2)
    REVIEW_CARDS_PER_CONVERSATION = 5
    SM2_DEFAULT_EASINESS = 2.5
    SM2_MIN_EASINESS = 1.3

    # 知识图谱
    GRAPH_MAX_NODES = 50

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "study-assistant-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 72
