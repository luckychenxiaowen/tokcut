"""tokcut 缓存模块 —— 语义缓存层。

使用 sentence-transformers 将用户请求转为向量嵌入，基于余弦相似度检索
命中缓存的响应。支持内存和 SQLite 两种后端，可配置相似度阈值和 TTL。
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SemanticCache:
    """语义缓存，通过 embedding 相似度匹配来返回缓存的 LLM 响应。

    Attributes:
        threshold: 余弦相似度阈值 (0-1)，超过此值视为命中。
        ttl: 缓存有效期（秒）。
        backend: 后端类型，'memory' 或 'sqlite'。
        model: sentence-transformers 模型实例。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化语义缓存。

        Args:
            config: 缓存配置字典，包含以下键：
                - similarity_threshold (float): 相似度阈值，默认 0.95。
                - backend (str): 'memory' 或 'sqlite'，默认 'memory'。
                - ttl_minutes (int): 缓存 TTL（分钟），默认 60。
                - sqlite_path (str): SQLite 数据库路径，默认 './cache.db'。
        """
        self.threshold: float = config.get("similarity_threshold", 0.95)
        self.backend: str = config.get("backend", "memory")
        self.ttl: float = config.get("ttl_minutes", 60) * 60
        self._model: Optional[SentenceTransformer] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self._conn = None

        if self.backend == "sqlite":
            import sqlite3

            db_path = config.get("sqlite_path", "./cache.db")
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._init_db()

    @property
    def model(self) -> SentenceTransformer:
        """延迟加载 sentence-transformers 模型。"""
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _init_db(self) -> None:
        """初始化 SQLite 缓存表。"""
        if self._conn is None:
            return
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                embedding BLOB,
                response TEXT,
                timestamp REAL
            )
        """)
        self._conn.commit()

    def _compute_key(self, messages: List[Dict[str, str]]) -> str:
        """为消息列表计算 SHA-256 哈希键。

        Args:
            messages: 聊天消息列表。

        Returns:
            hex 格式的哈希字符串。
        """
        content = json.dumps(
            [{k: msg[k] for k in ["role", "content"]} for msg in messages],
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _embed(self, text: str) -> np.ndarray:
        """将文本转为向量嵌入。

        Args:
            text: 输入文本。

        Returns:
            numpy 向量数组。
        """
        return self.model.encode(text)

    def get(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """查询缓存，返回命中的响应。

        Args:
            messages: 用户请求消息列表。

        Returns:
            如果命中，返回缓存的完整响应字典；否则返回 None。
        """
        query_text = " ".join(
            [m["content"] for m in messages if m.get("role") == "user"]
        )
        if not query_text:
            return None

        try:
            query_emb = self._embed(query_text)
        except Exception as e:
            logger.warning(f"Failed to embed query: {e}")
            return None

        if self.backend == "memory":
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if time.time() - entry["timestamp"] > self.ttl:
                    expired_keys.append(key)
                    continue
                sim = self._cosine_similarity(query_emb, entry["embedding"])
                if sim >= self.threshold:
                    return entry["response"]
            for key in expired_keys:
                del self.memory_cache[key]
        else:
            try:
                cur = self._conn.execute(
                    "SELECT key, embedding, response, timestamp FROM cache"
                )
                for row in cur.fetchall():
                    if time.time() - row[3] > self.ttl:
                        continue
                    stored_emb = self._deserialize_embedding(row[1])
                    sim = self._cosine_similarity(query_emb, stored_emb)
                    if sim >= self.threshold:
                        return json.loads(row[2])
            except Exception as e:
                logger.warning(f"Failed to query SQLite cache: {e}")

        return None

    def set(
        self, messages: List[Dict[str, str]], response: Dict[str, Any]
    ) -> None:
        """将响应存入缓存。

        Args:
            messages: 原始请求消息列表。
            response: 完整的响应字典。
        """
        query_text = " ".join(
            [m["content"] for m in messages if m.get("role") == "user"]
        )
        if not query_text:
            return

        try:
            emb = self._embed(query_text)
            key = self._compute_key(messages)
        except Exception as e:
            logger.warning(f"Failed to embed/serialize cache entry: {e}")
            return

        payload = {
            "key": key,
            "embedding": emb,
            "response": response,
            "timestamp": time.time(),
        }

        if self.backend == "memory":
            self.memory_cache[key] = payload
        elif self._conn is not None:
            try:
                self._conn.execute(
                    "INSERT OR REPLACE INTO cache (key, embedding, response, timestamp) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        key,
                        self._serialize_embedding(emb),
                        json.dumps(response),
                        time.time(),
                    ),
                )
                self._conn.commit()
            except Exception as e:
                logger.warning(f"Failed to write to SQLite cache: {e}")

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算两个向量的余弦相似度。

        Args:
            a: 第一个向量。
            b: 第二个向量。

        Returns:
            余弦相似度值 (0-1)。
        """
        return float((a @ b) / (a.dot(a) ** 0.5 * b.dot(b) ** 0.5))

    @staticmethod
    def _serialize_embedding(emb: np.ndarray) -> bytes:
        """将 numpy 向量序列化为字节流。"""
        return emb.tobytes()

    @staticmethod
    def _deserialize_embedding(blob: bytes) -> np.ndarray:
        """从字节流反序列化 numpy 向量。"""
        return np.frombuffer(blob, dtype=np.float32)
