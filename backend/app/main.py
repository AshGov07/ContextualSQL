from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import upload
from app.routes import session
from app.routes import schema
from app.routes import chat
from app.routes import database_tree
from app.routes import chat_ai
from app.routes import export
from app.routes import settings


app = FastAPI(
    title="Text To SQL RAG"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    session.router,
    prefix="/api/session",
    tags=["Session"]
)

app.include_router(
    upload.router,
    prefix="/api/upload",
    tags=["Upload"]
)
app.include_router(
    schema.router,
    prefix="/api/schema",
    tags=["Schema"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat"]
)

app.include_router(
    database_tree.router,
    prefix="/api/database-tree",
    tags=["Database Tree"]
)
app.include_router(
    chat_ai.router,
    prefix="/api/ai",
    tags=["AI"]
)

app.include_router(
    export.router,
    prefix="/api/export",
    tags=["Export"]
)

app.include_router(
    settings.router,
    prefix="/api/settings",
    tags=["Settings"]
)

@app.get("/")
def health():
    return {
        "status": "running"
    }