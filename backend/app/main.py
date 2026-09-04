"""
FastAPI application entry point.
Configures CORS, mounts API routers, and handles startup lifecycle events.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # --- STARTUP ---
    # Import all models so SQLAlchemy registers them with Base.metadata
    from app.models import user, doctor, schedule, appointment, triage_session  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("[Startup] Database tables created/verified.")

    # Seed initial data (doctors, slots, guidelines)
    from app.db.init_db import seed_database
    seed_database()

    # Initialize RAG knowledge base
    try:
        from app.services.rag_service import initialize_kb
        initialize_kb()
    except Exception as e:
        print(f"[Startup] RAG initialization skipped: {e}")

    yield
    # --- SHUTDOWN ---
    print("[Shutdown] Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade API for AI-powered Healthcare Triage, Appointment Scheduling, and Patient Engagement",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
from app.api.v1.api_router import api_router  # noqa: E402
app.include_router(api_router)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
