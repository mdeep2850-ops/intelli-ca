from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logger import logger
from app.api import chat, document, rag, agent

# Create tables in SQLite if they don't exist
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelli-CA AI Assistant API",
    version="0.1.0"
)

# Set up CORS
origins = ["*"] if settings.DEBUG else [settings.FRONTEND_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(document.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])

@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}
