import json
from pathlib import Path
from typing import Dict, List

import chromadb
from sentence_transformers import SentenceTransformer

from .chunking import chunk_pdfs, save_chunks
from .settings import CHROMA_DIR, CHUNKS_FILE, COLLECTION_NAME, DATA_DIR, EMBEDDING_MODEL


def load_chunks(path: Path) -> List[Dict]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def save_manifest(data: Dict) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHROMA_DIR / "manifest.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def load_manifest() -> Dict:
    path = CHROMA_DIR / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _ids(chunks: List[Dict]) -> List[str]:
    return [f"{chunk['source']}:{chunk['chunk_id']}:{index}" for index, chunk in enumerate(chunks)]


def _metadatas(chunks: List[Dict]) -> List[Dict]:
    rows = []
    for chunk in chunks:
        title = chunk.get("title", "") or ""
        if not title or title.lower() == "document":
            first_line = chunk["text"].split("\n")[0].strip()
            title = first_line[:80] if first_line else "document"

        rows.append(
            {
                "source": chunk.get("source", "unknown"),
                "chunk_id": str(chunk.get("chunk_id", "")),
                "title": title,
                "strategy": chunk.get("strategy", "unknown"),
                "char_count": int(chunk.get("char_count", 0)),
                "word_count": int(chunk.get("word_count", 0)),
            }
        )
    return rows


def get_client() -> chromadb.PersistentClient:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _add_batches(collection, ids, docs, metas, embeddings, batch_size=500) -> None:
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=docs[start:end],
            metadatas=metas[start:end],
            embeddings=embeddings[start:end],
        )


def build(chunks: List[Dict], reset: bool = False) -> chromadb.Collection:
    client = get_client()

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [chunk["text"] for chunk in chunks]
    ids = _ids(chunks)
    metadatas = _metadatas(chunks)

    embeddings = model.encode(
        texts,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    _add_batches(collection, ids, texts, metadatas, embeddings)

    save_manifest(
        {
            "chunks_file": str(CHUNKS_FILE),
            "collection": COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL,
            "num_chunks": len(chunks),
        }
    )

    return collection


def build_index_from_file(
    chunks_file: Path = CHUNKS_FILE,
    reset: bool = False,
) -> chromadb.Collection:
    """Load chunks from disk and build the persistent collection."""
    if not chunks_file.exists():
        raise FileNotFoundError(chunks_file)

    chunks = load_chunks(chunks_file)
    return build(chunks, reset=reset)


def rebuild_from_pdfs(
    input_dir: Path = DATA_DIR,
    chunks_file: Path = CHUNKS_FILE,
    reset: bool = True,
) -> chromadb.Collection:
    """Rechunk all PDFs, save the chunks JSON, and rebuild the index."""
    chunks = chunk_pdfs(input_dir)
    save_chunks(chunks, chunks_file)
    return build(chunks, reset=reset)
