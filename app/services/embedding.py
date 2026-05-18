"""
语义去重服务 - 使用GLM Embedding API和LanceDB
"""
import os
import hashlib
from typing import List, Dict, Optional
import httpx
import lancedb
from lancedb.pydantic import LanceModel, Vector
import pydantic
from pathlib import Path

from config import LANCEDB_PATH, GLM_API_KEY, GLM_API_URL, GLM_EMBED_MODEL


# LanceDB表结构
class EmbeddingRecord(LanceModel):
    """向量存储记录"""
    id: str  # 文本hash作为ID
    text: str
    vector: Vector(2048)


class EmbeddingService:
    """GLM Embedding服务"""

    def __init__(self):
        self.api_key = GLM_API_KEY
        self.api_url = GLM_API_URL
        self.model = GLM_EMBED_MODEL
        self.db_path = str(LANCEDB_PATH)

        # 内存缓存 (避免频繁查询数据库)
        self._cache: Dict[str, List[float]] = {}

        # 初始化LanceDB
        self._db: Optional[lancedb.DBConnection] = None
        self._table: Optional[lancedb.table.Table] = None

    @property
    def db(self) -> lancedb.DBConnection:
        """懒加载数据库连接"""
        if self._db is None:
            Path(self.db_path).mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(self.db_path)
        return self._db

    @property
    def table(self) -> lancedb.table.Table:
        """懒加载向量表"""
        if self._table is None:
            try:
                self._table = self.db.open_table("embeddings")
            except Exception:
                self._table = self.db.create_table("embeddings", schema=EmbeddingRecord)
        return self._table

    def _text_hash(self, text: str) -> str:
        """生成文本hash作为ID"""
        return hashlib.md5(text.encode()).hexdigest()

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本向量
        优先级: 内存缓存 -> LanceDB -> API调用
        """
        if not text.strip():
            return None

        text_hash = self._text_hash(text)

        # 1. 检查内存缓存
        if text_hash in self._cache:
            return self._cache[text_hash]

        # 2. 检查LanceDB
        try:
            results = self.table.search().where(f"id = '{text_hash}'").limit(1).to_pandas()
            if not results.empty:
                vector = results.iloc[0]["vector"].tolist()
                self._cache[text_hash] = vector
                return vector
        except Exception:
            pass

        # 3. 调用GLM API
        vector = await self._call_api(text)
        if vector:
            # 存入缓存
            self._cache[text_hash] = vector
            # 存入LanceDB
            try:
                record = EmbeddingRecord(
                    id=text_hash,
                    text=text[:1000],  # 限制存储长度
                    vector=vector
                )
                self.table.add([record])
            except Exception as e:
                print(f"LanceDB存储失败: {e}")

        return vector

    async def _call_api(self, text: str) -> Optional[List[float]]:
        """调用GLM Embedding API"""
        if not self.api_key:
            print("警告: GLM_API_KEY未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": text
                    }
                )

                if resp.status_code != 200:
                    print(f"GLM API错误: {resp.status_code} - {resp.text}")
                    return None

                data = resp.json()
                return data["data"][0]["embedding"]

        except Exception as e:
            print(f"GLM API调用失败: {e}")
            return None

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    async def deduplicate(
        self,
        items: List[Dict],
        threshold: float = 0.85,
        text_field: str = "title"
    ) -> List[Dict]:
        """
        语义去重
        返回相似度低于阈值的内容 (保留第一个出现的项)

        Args:
            items: 待去重的内容列表
            threshold: 相似度阈值, 高于此值视为重复
            text_field: 用于比较的文本字段

        Returns:
            去重后的内容列表
        """
        if not items:
            return []

        result = []
        seen_vectors: List[List[float]] = []

        for item in items:
            text = item.get(text_field, "")
            if not text:
                result.append(item)
                continue

            vector = await self.get_embedding(text)
            if not vector:
                result.append(item)
                continue

            # 检查是否与已有内容相似
            is_duplicate = False
            for seen in seen_vectors:
                similarity = self._cosine_similarity(vector, seen)
                if similarity >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                result.append(item)
                seen_vectors.append(vector)

        return result


# 全局单例
_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取Embedding服务单例"""
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service


# 便捷函数
async def get_embedding(text: str) -> Optional[List[float]]:
    """获取文本向量"""
    return await get_embedding_service().get_embedding(text)


async def deduplicate(
    items: List[Dict],
    threshold: float = 0.85,
    text_field: str = "title"
) -> List[Dict]:
    """
    语义去重
    返回相似度低于阈值的内容
    """
    return await get_embedding_service().deduplicate(items, threshold, text_field)