"""FastAPI application initialization."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import documents, chat, analyze, evals
from .middleware import setup_cors, log_requests

app = FastAPI(
    title="Investment Research AI",
    description="AI-powered financial document analysis platform",
    version="1.0.0",
)

# Setup middleware
setup_cors(app)
app.middleware("http")(log_requests)

# Include routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(analyze.router)
app.include_router(evals.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats():
    """System statistics."""
    return {"stats": {}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
