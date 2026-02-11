"""
FastAPI application entry point for AI Paperwork Co-pilot backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import health, documents, facts, autofill, unified_workflow, unified_workflow
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()

app = FastAPI(
    title="AI Paperwork Co-pilot API",
    description="Backend API for AI-powered paperwork assistance",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(facts.router, prefix="/api/v1/facts", tags=["facts"])
app.include_router(autofill.router, prefix="/api/v1/autofill", tags=["autofill"])
app.include_router(unified_workflow.router, prefix="/api/v1/workflow", tags=["unified workflow"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Paperwork Co-pilot API"}

