from typing import Any, Dict, List

import chromadb
from groq import Groq
from sentence_transformers import CrossEncoder, SentenceTransformer

from .settings import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    RERANKER_MODEL,
    RERANK_TOP_K,
    RETRIEVE_K,
)


_EMBED_CACHE: Dict[str, SentenceTransformer] = {}
_RERANK_CACHE: Dict[str, CrossEncoder] = {}


def _embed_model() -> SentenceTransformer:
    if EMBEDDING_MODEL not in _EMBED_CACHE:
        _EMBED_CACHE[EMBEDDING_MODEL] = SentenceTransformer(EMBEDDING_MODEL)
    return _EMBED_CACHE[EMBEDDING_MODEL]


def _rerank_model() -> CrossEncoder:
    if RERANKER_MODEL not in _RERANK_CACHE:
        _RERANK_CACHE[RERANKER_MODEL] = CrossEncoder(RERANKER_MODEL)
    return _RERANK_CACHE[RERANKER_MODEL]


def _collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise FileNotFoundError("Chroma collection not found. Build the index first.") from exc


def _retrieve_one(query: str, k: int) -> List[Dict]:
    embedding = _embed_model().encode([query], normalize_embeddings=True).tolist()
    result = _collection().query(query_embeddings=embedding, n_results=k)
    hits = []

    for doc_id, doc, meta, dist in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        hits.append(
            {
                "id": doc_id,
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_id": meta.get("chunk_id", "?"),
                "title": meta.get("title", "document"),
                "score": float(1.0 - dist),
            }
        )
    return hits


def _deduplicate(hits: List[Dict]) -> List[Dict]:
    seen: Dict[str, Dict] = {}
    for hit in hits:
        if hit["id"] not in seen or hit["score"] > seen[hit["id"]]["score"]:
            seen[hit["id"]] = hit
    return list(seen.values())


def rerank(hits: List[Dict], query: str, top_k: int) -> List[Dict]:
    pairs = [(query, hit["text"]) for hit in hits]
    scores = _rerank_model().predict(pairs)
    for hit, score in zip(hits, scores):
        hit["rerank_score"] = float(score)
    hits.sort(key=lambda item: item["rerank_score"], reverse=True)
    return hits[:top_k]


def remove_similar_chunks(hits: List[Dict]) -> List[Dict]:
    seen_texts = set()
    unique_hits = []

    for hit in hits:
        text_key = hit["text"][:200]
        if text_key in seen_texts:
            continue

        seen_texts.add(text_key)
        unique_hits.append(hit)

    return unique_hits


def retrieve(question: str, use_rerank: bool = True) -> List[Dict]:
    all_hits = _deduplicate(_retrieve_one(question, RETRIEVE_K))

    if use_rerank:
        all_hits = rerank(all_hits, question, RERANK_TOP_K)
        all_hits = remove_similar_chunks(all_hits)
    else:
        all_hits.sort(key=lambda item: item["score"], reverse=True)
        all_hits = all_hits[:RERANK_TOP_K]

    return all_hits


_SYSTEM_PROMPT = """
You are a research-paper assistant.

Your task is to answer ONLY from the provided retrieved context.
Do NOT use prior knowledge, world knowledge, assumptions, or external information.

Rules:
1. Answer strictly based on the retrieved context.
2. If the answer is not fully supported by the context, say:
   "The provided context does not contain enough information to answer this question."
3. Do not infer, speculate, or fill gaps with outside knowledge.
4. Do not add background information unless explicitly present in the context.
5. Prefer quoting or closely paraphrasing the source material.
6. Keep responses precise, technical, and concise.
7. Cite supporting chunks inline using [source] format.
8. If multiple context chunks disagree, mention the conflict instead of resolving it yourself.
9. Never fabricate citations, equations, experimental results, or claims.
10. If the question is unrelated to the provided context, refuse politely.
"""


def _build_context(hits: List[Dict]) -> str:
    parts = []
    for index, hit in enumerate(hits, 1):
        parts.append(f"[{index}] Source: {hit['source']} | Section: {hit['title']}\n{hit['text']}")
    return "\n\n---\n\n".join(parts)


def answer(question: str, use_rerank: bool = True) -> Dict[str, Any]:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    client = Groq(api_key=GROQ_API_KEY)
    hits = retrieve(question, use_rerank)
    context = _build_context(hits)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return {"answer": response.choices[0].message.content, "sources": hits}
