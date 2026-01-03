"""FastAPI application entry point with OpenAPI configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.routes import chat, session, appointments, patients, heuristics, admin


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    from src.core.database import init_db

    # Initialize database tables
    await init_db()
    # TODO: Initialize agent system
    yield
    # Shutdown
    from src.core.database import close_db

    # Close database connections
    await close_db()
    # TODO: Cleanup agent resources


app = FastAPI(
    title="PearlFlow API",
    description="""
    🦷 **PearlFlow** - Intelligent Dental Practice AI Assistant

    Multi-agent orchestration system for dental practice management with:
    - **Root Receptionist Agent**: Intent classification and delegation
    - **IntakeSpecialist Agent**: Patient triage and symptom assessment
    - **ResourceOptimiser Agent**: Intelligent appointment scheduling

    ## Features
    - Agentic AI-powered patient intake and triage
    - Revenue-based appointment optimization
    - Proactive patient engagement and negotiation
    - Real-time SSE streaming for chat responses
    - AHPRA compliance and Australian Privacy Principles adherence

    ## Authentication
    Use your clinic API key in the `X-API-Key` header for authenticated requests.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "version": "1.0.0"}


# Include routers
app.include_router(session.router, prefix="/session", tags=["Session"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(heuristics.router, prefix="/heuristics", tags=["Heuristics"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
