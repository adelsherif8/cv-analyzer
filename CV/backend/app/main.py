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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
