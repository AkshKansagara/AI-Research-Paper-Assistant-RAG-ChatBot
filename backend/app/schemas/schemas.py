from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    use_rerank: bool = True


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1)
    use_rerank: bool = True


class SourceChunk(BaseModel):
    id: str
    text: str
    source: str
    chunk_id: str
    title: str
    score: float
    rerank_score: Optional[float] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]


class RetrieveResponse(BaseModel):
    question: str
    sources: List[SourceChunk]


class ReindexRequest(BaseModel):
    reset: bool = True


class ReindexResponse(BaseModel):
    chunks_file: str
    collection: str
    embedding_model: str
    num_chunks: int
