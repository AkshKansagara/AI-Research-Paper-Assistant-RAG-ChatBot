import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = PROJECT_ROOT / "data"
CHUNKS_FILE = PROJECT_ROOT / "chunks" / "chunks.json"
CHROMA_DIR = PROJECT_ROOT / "vectorstores" / "chroma"

COLLECTION_NAME = "research_papers"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
RERANKER_MODEL = os.getenv("RERANKER_MODEL")

CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS"))
OVERLAP_TOKENS = int(os.getenv("OVERLAP_TOKENS"))

RETRIEVE_K = int(os.getenv("RETRIEVE_K"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
