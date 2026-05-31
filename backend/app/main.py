from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.utils.helpers import ensure_directory_exists
from backend.app.database import engine, Base
from backend.app.routes import auth, interview, history, performance

# Create all database tables on application launch (automatic migrations)
try:
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize database: {e}")
    raise

# Initialize the main FastAPI application instance
app = FastAPI(
    title="AI Interview Assistant API",
    description="Production-ready mock interview simulator with JWT auth, ATS parsing, and adaptive Q&A",
    version="2.0.0"
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, lock this down to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """
    Map python ValueError exceptions to client-friendly HTTP 400 Bad Requests.
    """
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

# ---------------------------------------------------------------------------
# Startup / Shutdown Events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    Executes automatically on server startup. Initializes uploads folder.
    """
    logger.info("Running post-initialization startup configurations...")
    ensure_directory_exists(settings.upload_dir)
    logger.info("AI Interview Assistant Backend is ready.")

# ---------------------------------------------------------------------------
# Routers Registration
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(performance.router, prefix="/api")

@app.get("/health", tags=["health"])
async def health_check():
    """
    Dedicated health check endpoint for deployment monitoring.
    """
    return {"status": "healthy"}

@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint serving application metadata and health status.
    """
    return {
        "status": "healthy",
        "app": "AI Interview Assistant API",
        "version": "2.0.0",
        "database_url": settings.database_url,
        "gemini_configured": bool(settings.gemini_api_key)
    }
