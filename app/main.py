"""
isiXhosa Tech Glossary API

Run locally:
    uvicorn app.main:app --reload
API docs:  http://localhost:8000/docs
Website:   http://localhost:8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import suggestions, terms

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="isiXhosa Tech Glossary",
    description="English and isiXhosa terms for computing and technology.",
    version="1.0.0",
    lifespan=lifespan,
)

# Let other websites call the public API from the browser (read-only use)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

app.include_router(terms.router)
app.include_router(suggestions.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def website():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
