from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    app_name: str = "RAG Chatbot"
    app_env: str = "development"
    debug: bool = True

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 3115
    qdrant_collection_name: str = "rag_documents"
    qdrant_vector_size: int = 768

    # MinerU
    mineru_output_dir: str = "./data/mineru_output"

    # Upload
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 100
    allowed_extensions: str = "pdf,docx,txt,md"

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_results: int = 5
    similarity_threshold: float = 0.3


    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    def ensure_dirs(self):
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.mineru_output_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
