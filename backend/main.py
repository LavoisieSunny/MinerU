"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.core.config import settings
from backend.core.logger import logger

app = FastAPI(
    title=settings.app_name,
    description="RAG Chatbot powered by MinerU, Ollama, and Qdrant",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logger.info(f"🚀 {settings.app_name} starting up (env={settings.app_env})")
    logger.info(f"   LLM model  : {settings.ollama_llm_model}")
    logger.info(f"   Embed model: {settings.ollama_embed_model}")
    logger.info(f"   Qdrant     : {settings.qdrant_host}:{settings.qdrant_port}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=3110, reload=settings.debug)
