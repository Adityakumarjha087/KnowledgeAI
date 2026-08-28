from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.metrics import router as metrics_router
from app.models.base import Base
from app.core.database import engine

# Automatically create all database tables on application boot (crucial for SQLite)
Base.metadata.create_all(bind=engine)

# Hide API docs in production to avoid schema leakage
_docs_url = "/docs" if settings.APP_ENV != "production" else None
_redoc_url = "/redoc" if settings.APP_ENV != "production" else None
_openapi_url = "/openapi.json" if settings.APP_ENV != "production" else None

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Knowledge Assistant API",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)


# CORS: locked to explicit origins set via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")






@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "status": "online"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the details of the exception
    # (in production, log using a proper logger setup)
    print(f"Global exception caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact the administrator."},
    )
