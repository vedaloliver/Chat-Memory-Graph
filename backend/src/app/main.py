from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes_chat import router as chat_router
from src.app.core.config import get_settings
from src.app.llm import AppError
from src.app.db.init_db import init_db

# Get application settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A simple LLM service with persistent conversation storage",
    version="0.1.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the database
init_db()

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])


# Add exception handler for AppError
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """
    Global exception handler for AppError.
    Returns appropriate status code and error message.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint to verify the service is running.
    """
    return {"status": "ok"}


# Root route redirects to docs
@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint redirects to API documentation.
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


# For direct execution with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
