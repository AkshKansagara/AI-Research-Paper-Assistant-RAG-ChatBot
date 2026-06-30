# RAG Chatbot

Full-stack research-paper RAG chatbot with a FastAPI backend and a React/Vite frontend. The backend chunks PDF files, stores embeddings in a persistent Chroma collection, retrieves relevant source chunks, optionally reranks them, and asks Groq to answer only from the retrieved context.

## Features

- PDF ingestion from the project-level `data/` directory
- Text cleaning, section-aware chunking, and PyMuPDF fallback extraction
- SentenceTransformer embeddings stored in ChromaDB
- Optional CrossEncoder reranking for retrieved chunks
- Groq chat completion for grounded answers
- React chat UI with source chunks attached to assistant responses
- Reindex endpoint for rebuilding the PDF index from the API

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/routes.py
|   |   |-- core/chunking.py
|   |   |-- core/indexing.py
|   |   |-- core/rag.py
|   |   `-- main.py
|   |-- .env.example
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |-- .env.example
|   `-- package.json
|-- data/              # Put source PDFs here
|-- chunks/            # Generated chunks.json
`-- vectorstores/      # Generated Chroma database
```

`data/`, `chunks/`, and `vectorstores/` are generated/local runtime directories and are ignored by Git.

## Requirements

- Python 3.10+
- Node.js 20+ recommended for the current Vite/React toolchain
- A Groq API key
- PDF files to index

## Backend Setup

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `backend/.env` with real values:

```env
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=your-groq-model

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

CHUNK_TOKENS=350
OVERLAP_TOKENS=60

RETRIEVE_K=12
RERANK_TOP_K=5
```

The backend also supports `FRONTEND_ORIGINS` as a comma-separated list. If it is not set, local Vite origins are allowed by default.

## Add Documents

From the project root, create the data directory and add PDFs:

```bash
mkdir -p data
```

If your terminal is inside `backend/`, the same directory is `../data`.

## Run The Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the API docs at:

```text
http://localhost:8000/docs
```

## Build Or Rebuild The Index

After adding PDFs to `data/`, rebuild the index:

```bash
curl -X POST http://localhost:8000/api/reindex \
  -H "Content-Type: application/json" \
  -d '{"reset": true}'
```

This creates or updates:

- `chunks/chunks.json`
- `vectorstores/chroma/`
- `vectorstores/chroma/manifest.json`

The first run can take time because embedding and reranking models may need to download.

## Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
```

`frontend/.env` should point to the backend:

```env
VITE_API_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

Open the URL printed by Vite, usually:

```text
http://localhost:5173
```

## API Endpoints

### `POST /api/query`

Retrieves source chunks and returns a grounded answer.

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the paper about?", "use_rerank": true}'
```

### `POST /api/retrieve`

Returns retrieved source chunks without generating an answer.

```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "What method is used?", "use_rerank": true}'
```

### `POST /api/reindex`

Rechunks all PDFs and rebuilds the Chroma index.

```bash
curl -X POST http://localhost:8000/api/reindex \
  -H "Content-Type: application/json" \
  -d '{"reset": true}'
```

## Useful Commands

Backend:

```bash
cd backend
source .venv/bin/activate
python -m compileall -q app
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
npm run dev
```

## Troubleshooting

- `GROQ_API_KEY not set in .env`: create `backend/.env` and set a valid key.
- `Chroma collection not found. Build the index first.`: run `POST /api/reindex` after adding PDFs to `data/`.
- Empty or poor retrieval results: confirm PDFs are in the project-level `data/` folder, then rebuild with `{"reset": true}`.
- Missing frontend API URL: create `frontend/.env` with `VITE_API_URL=http://localhost:8000`.
- Slow first request: local embedding and reranking models may be loading for the first time.

## Notes

The assistant is instructed to answer only from retrieved context. If the indexed documents do not support an answer, the backend prompt tells the model to say that the provided context does not contain enough information.
