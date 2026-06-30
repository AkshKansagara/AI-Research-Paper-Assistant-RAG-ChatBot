from fastapi import APIRouter, HTTPException

from ..core.indexing import load_manifest, rebuild_from_pdfs
from ..core.rag import answer, retrieve
from ..schemas.schemas import (
    QueryRequest,
    QueryResponse,
    ReindexRequest,
    ReindexResponse,
    RetrieveRequest,
    RetrieveResponse,
)

router = APIRouter()


@router.post("/api/query", response_model=QueryResponse)
def query_route(payload: QueryRequest) -> QueryResponse:
    try:
        result = answer(payload.question, use_rerank=payload.use_rerank)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return QueryResponse(
        question=payload.question,
        answer=result["answer"],
        sources=result["sources"],
    )


@router.post("/api/retrieve", response_model=RetrieveResponse)
def retrieve_route(payload: RetrieveRequest) -> RetrieveResponse:
    try:
        sources = retrieve(payload.question, use_rerank=payload.use_rerank)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RetrieveResponse(question=payload.question, sources=sources)


@router.post("/api/reindex", response_model=ReindexResponse)
def reindex_route(payload: ReindexRequest) -> ReindexResponse:
    try:
        rebuild_from_pdfs(reset=payload.reset)
        manifest = load_manifest()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReindexResponse(
        chunks_file=str(manifest.get("chunks_file", "")),
        collection=str(manifest.get("collection", "")),
        embedding_model=str(manifest.get("embedding_model", "")),
        num_chunks=int(manifest.get("num_chunks", 0)),
    )
