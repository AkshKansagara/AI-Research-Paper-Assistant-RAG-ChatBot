from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .core.settings import FRONTEND_ORIGINS


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Chatbot Backend",
        version="1.0.0",
        description="FastAPI backend for the research-paper RAG chatbot.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=FRONTEND_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
