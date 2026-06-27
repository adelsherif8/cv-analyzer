from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import create_data_directories, settings
from app.routers import roles, files, analyze

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_data_directories()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(
    title="CV Analyzer MVP",
    description="AI-powered CV analysis for HR teams",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# Allowed origins come from the ALLOWED_ORIGINS env var (comma-separated).
# Defaults to local dev; set it to your deployed frontend URL(s) in production.
import os
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight health check for uptime pings / platform health probes
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

# Include routers
app.include_router(roles.router, prefix="/roles", tags=["Roles"])
app.include_router(files.router, prefix="/upload", tags=["File Upload"])
app.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])

@app.get("/")
async def root():
    return {"message": "CV Analyzer MVP API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_name": settings.MODEL_NAME,
        "data_dir": settings.DATA_DIR
    }
