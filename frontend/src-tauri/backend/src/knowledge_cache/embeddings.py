import numpy as np
from openai import OpenAI

from src.config import Config


class EmbeddingManager:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            type(self)._client = OpenAI(
                api_key=Config.ALIYUN_EMBEDDING_API_KEY,
                base_url=Config.ALIYUN_EMBEDDING_API_BASE,
            )

    @property
    def client(self):
        return type(self)._client

    def embed_text(self, text: str) -> list[float]:
        resp = self.client.embeddings.create(
            model=Config.ALIYUN_EMBEDDING_MODEL,
            input=text[:2048],
        )
        return resp.data[0].embedding

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def find_best_match(self, query: str, records: list[dict],
                        threshold: float = None) -> tuple[dict | None, float]:
        from src.config import Config
        threshold = threshold or Config.CACHE_SIMILARITY_THRESHOLD
        query_emb = self.embed_text(query)
        best_score = 0.0
        best_record = None

        query_len = len(query_emb)
        for record in records:
            stored_emb = record.get("embedding")
            if stored_emb:
                stored_vec = np.frombuffer(stored_emb, dtype=np.float32).tolist()
                if len(stored_vec) != query_len:
                    continue  # 旧版 embedding 维度不同，跳过
                score = self.cosine_similarity(query_emb, stored_vec)
                if score > best_score:
                    best_score = score
                    best_record = record

        if best_score >= threshold:
            return best_record, best_score
        return None, best_score
