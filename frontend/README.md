# RAG Frontend

This is the React frontend for the research-paper RAG chatbot. It sends questions to the FastAPI backend at `/api/query` and renders the answer with retrieved source chunks.

## Setup

Create `frontend/.env` from `frontend/.env.example` and set the backend URL if needed:

```bash
VITE_API_URL=http://localhost:8000
```

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
